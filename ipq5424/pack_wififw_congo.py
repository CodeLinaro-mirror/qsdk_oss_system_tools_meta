#!/usr/bin/env python3
#######################################################################
# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: ISC
#######################################################################
# pack_wififw_congo.py — build wifi_fw_ipq5424_congo_v2_squashfs.img for CRM meta builds.
#
# The squashfs contains a fig/ subdir with Congo FW blobs. wififw-mount.sh
# symlinks /lib/firmware/$arch/WIFI_FW/fig/* -> /lib/firmware/fig/ at boot.
#
# Required files in the current directory (staged from WLAN.CNG FW build):
#
#   amss20.bin                        — cnss_ram_v2_TO_link_patched/.../amss20.bin
#   Data20.msc                        — wlan_diag_v2/Data20.msc
#   phy_ucode20.elf                   — phyucode_binary/congo2/phy_ucode20.elf
#   aux_ucode20.elf                   — auxucode_binary/congo2/aux_ucode20.elf
#   bdwlan.elf                        — bdf/bin/bdwlan.elf (or renamed from bdwlan.e1c)
#   regdb.bin                         — bdf/bin/regdb.bin
#   qdss_trace_config_v2.cfg          — wlanhw_debug/.../qdss_trace_config_v2.cfg
#   qdss_trace_config_debug_v2.cfg
#   qdss_trace_config_perf_v2.cfg
#   qdss_trace_config_etm_v2.cfg      (optional)
#
# Output:
#   wifi_fw_ipq5424_congo_v2_squashfs.img  — squashfs containing only fig/

import datetime
import multiprocessing
import os
import shutil
import subprocess
import sys
import tempfile

OUTPUT = 'wifi_fw_ipq5424_congo_v2_squashfs.img'

REQUIRED_FILES = [
    'amss20.bin',
    'Data20.msc',
    'phy_ucode20.elf',
    'aux_ucode20.elf',
    'bdwlan.elf',
    'regdb.bin',
    'qdss_trace_config_v2.cfg',
    'qdss_trace_config_debug_v2.cfg',
    'qdss_trace_config_perf_v2.cfg',
]
OPTIONAL_FILES = ['qdss_trace_config_etm_v2.cfg']


def log(msg):
    print(msg, flush=True)


def main():
    log('==== pack_wififw_congo.py — %s ====' % datetime.datetime.now().isoformat())

    mksqfs = shutil.which('mksquashfs')
    if not mksqfs:
        log('ERROR: mksquashfs not found in PATH')
        sys.exit(1)

    missing = [f for f in REQUIRED_FILES if not os.path.isfile(f)]
    if missing:
        for f in missing:
            log('ERROR: missing Congo FW file: %s' % f)
        sys.exit(1)

    work_dir = tempfile.mkdtemp(prefix='pack_wififw_congo.')
    try:
        fig_dir = os.path.join(work_dir, 'tree', 'fig')
        os.makedirs(fig_dir)

        log('==== staging Congo FW under fig/ ====')
        for f in REQUIRED_FILES + [f for f in OPTIONAL_FILES if os.path.isfile(f)]:
            dst = os.path.join(fig_dir, os.path.basename(f))
            shutil.copy2(f, dst)
            os.chmod(dst, 0o644)
            log('  %s' % f)

        log('==== mksquashfs -> %s ====' % OUTPUT)
        if os.path.exists(OUTPUT):
            os.remove(OUTPUT)

        tree_dir = os.path.join(work_dir, 'tree')
        cmd = [mksqfs, tree_dir, OUTPUT,
               '-noappend', '-root-owned', '-comp', 'gzip',
               '-b', '256k', '-processors', str(multiprocessing.cpu_count())]
        ret = subprocess.call(cmd)
        if ret != 0:
            log('ERROR: mksquashfs failed (exit %d)' % ret)
            sys.exit(ret)

    finally:
        shutil.rmtree(work_dir, ignore_errors=True)

    log('==== done ====')
    size = os.path.getsize(OUTPUT)
    log('%s  %.1f MB' % (OUTPUT, size / 1024 / 1024))


if __name__ == '__main__':
    main()
