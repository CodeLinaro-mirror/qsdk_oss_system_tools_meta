#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ===========================================================================
# Copyright (c) 2024, Qualcomm Innovation Center, Inc. All rights reserved.
# SPDX-License-Identifier: ISC
# ===========================================================================

from __future__ import print_function
import xml.etree.ElementTree as ET
import os
import subprocess
import sys

PYTHON_EXECUTABLE = sys.executable or 'python'
import re
from getopt import getopt
from getopt import GetoptError
import json
import shutil
import struct

ARCH_NAME = ''

# Fallback DDR boot frequencies (in KHz) used only if not found in base DTS
DEFAULT_DDR3_BOOT_FREQ = 933000
DEFAULT_DDR4_BOOT_FREQ = 1600000
DEFAULT_DDR5_BOOT_FREQ = 2800000

# Architecture-specific configuration
ARCH_CONFIG = {
    "ipq5424": {"elf_address": "0x08CEE800", "align": None},
    "ipq5210": {"elf_address": "0x08CB5800", "align": "0x40"},
    "ipq9650": {"elf_address": "0x08CFB800", "align": "0x40"}
}

cdir = os.path.dirname("")
cdir = os.path.abspath(cdir)

XBL_CONFIG_RAW_ELF = cdir + "/xbl_config_raw.elf"

def parse_default_freqs_from_dts(dts_path):
    """Parse default DDR boot frequencies from the base DTS file.

    Returns a dict with keys 'ddr3_boot_freq', 'ddr4_boot_freq', 'ddr5_boot_freq'
    for whichever values are present in the DTS.
    """
    defaults = {}
    try:
        with open(dts_path, 'r') as f:
            content = f.read()
        for key in ['ddr3_boot_freq', 'ddr4_boot_freq', 'ddr5_boot_freq']:
            m = re.search(r'{}\s*=\s*<(\d+)>'.format(key), content)
            if m:
                defaults[key] = int(m.group(1))
    except Exception as e:
        print("WARNING: Could not parse default frequencies from DTS {0}: {1}".format(dts_path, e))
    return defaults

def update_CDT_segment(xbl_cfg_file_path, CDT_path):
    # Read the CDT content
    with open(CDT_path, 'rb') as new_file:
        CDT = new_file.read()
        CDT_file_size = os.path.getsize(CDT_path)

    with open(xbl_cfg_file_path, 'r+b') as elf_file:
        # Read an ELF header
        elf_file.seek(0)
        elf_header = elf_file.read(64)

        # Check if it's an elf file
        if elf_header[:4] != b'\x7fELF':
            return -1;

        # Get the pgm hdr table off and num of entries
        e_phoff = struct.unpack('Q', elf_header[32:40])[0]
        e_phnum = struct.unpack('H', elf_header[56:58])[0]

        # Iterate through pgm hdrs
        for i in range(e_phnum):
            elf_file.seek(e_phoff + i * 56)
            e_phdr = elf_file.read(56)

            # chk if it is a loadbale seg
            p_type = struct.unpack('I', e_phdr[0:4])[0]
            if p_type == 1:  # PT_LOAD
                p_offset = struct.unpack('Q', e_phdr[8:16])[0]
                p_filesz = struct.unpack('Q', e_phdr[32:40])[0]

                # Read the segment
                elf_file.seek(p_offset)
                segment = elf_file.read(3)

                # Check if starts with "CDT"
                if b"CDT" in segment:
                    print("Found CDT segment ")
                    if p_filesz != CDT_file_size:
                         print("CDT size mismatch")
                         return -1
                    elf_file.seek(p_offset)
                    elf_file.write(CDT)
                    return 0

        print("CDT not found in any loadable segment")
        return -1


def generate_rdp_dts(base_dts_path, board_name, ddr_type, boot_freq, output_dir, arch_name):
    """Generate RDP-specific DTS file with board-specific DDR frequency.

    Reads the base DTS template, substitutes only the boot frequency
    corresponding to ddr_type (e.g. 'DDR3', 'DDR4', 'DDR5'),
    and writes the result to
    qc-cust-<arch>-1.0_<board>.dts in output_dir.

    Returns (rdp_dts_path, rdp_dts_name).
    """
    with open(base_dts_path, 'r') as f:
        content = f.read()

    # Replace only the frequency for the active DDR type
    freq_key = ddr_type.lower() + '_boot_freq'
    content = re.sub(r'({}\s*=\s*<)\d+(>)'.format(freq_key),
                     r'\g<1>' + str(boot_freq) + r'\g<2>', content)

    rdp_dts_name = "qc-cust-{}-1.0_{}.dts".format(arch_name, board_name)
    rdp_dts_path = os.path.join(output_dir, rdp_dts_name)

    with open(rdp_dts_path, 'w') as f:
        f.write(content)

    return rdp_dts_path, rdp_dts_name


def main():

    global cdir
    global outputdir
    global ARCH_NAME
    global memory_profile
    global dtcDir

    memory_profile = "default"
    genqccfg = False
    if len(sys.argv) > 1:
        try:
            opts, args = getopt(sys.argv[1:], "c:o:m:", ["dtc_path=", "genqccfg", "mbnv="])
        except GetoptError as e:
            print("config file and output path are needed to generate xblcfg files")
            raise
        for option, value in opts:
            if option == "-c":
                file_path = value
            elif option == "-o":
                outputdir = value
            elif option == "-m":
                memory_profile = value
            elif option == "--dtc_path":
                dtcDir =  value
            elif option == "--genqccfg":
                genqccfg = True
            elif option == "--mbnv":
                mbn_version = value
    else:
        print("config file and output path are needed to generate xblcfg files")
        return -1

    tree = ET.parse(file_path)
    root = tree.getroot()

    machid = None
    board = None
    arch = root.find(".//data[@type='ARCH']/SOC")
    ARCH_NAME = str(arch.text)
    print(ARCH_NAME)

    # First validate architecture is supported
    if ARCH_NAME not in ARCH_CONFIG:
        print("ERROR: Unsupported architecture {0}".format(ARCH_NAME))
        return -1

    # Validate genqccfg flag: can only be false/not mentioned for ipq5424
    if ARCH_NAME != "ipq5424" and not genqccfg:
        print("ERROR: --genqccfg flag is required for {0} architecture".format(ARCH_NAME))
        return -1

    if ARCH_NAME == "ipq5424" and not genqccfg:
        srcDir = '$$/' + ARCH_NAME + '/xblconfig_json'
    else:
        srcDir = '$$/' + ARCH_NAME + '/qcconfig_json'
    srcDir = srcDir.replace('$$', cdir)
    if not os.path.exists(srcDir):
        os.makedirs(srcDir)

    xblconfigtool_path = '$$/scripts/XBLConfig/'
    xblconfigtool_path = xblconfigtool_path.replace('$$', cdir)
    xblconfigtool_gen = '$$/scripts/XBLConfig/GenXBLConfig.py'
    xblconfigtool_gen = xblconfigtool_gen.replace('$$', cdir)
    if ARCH_NAME == "ipq5424" and not genqccfg:
        xblconfig_path = '$$/xbl_config.elf'
    else:
        xblconfig_path = '$$/qc_config.elf'
    xblconfig_path = xblconfig_path.replace('$$', cdir)
    xblconfig_json = '$$/create_xbl_config.json'
    xblconfig_json = xblconfig_json.replace('$$', srcDir)

    #disassemble the xbl config
    print('Disassembling xblconfig')
    cmd = [PYTHON_EXECUTABLE, xblconfigtool_gen, '-d', xblconfig_path, '-fELF', '-o', srcDir, '--tools_path', xblconfigtool_path]
    print(cmd)
    prc = subprocess.Popen(cmd, cwd=cdir)
    prc.wait()
    dircet_CDT_update = 0

    if prc.returncode != 0:
        dircet_CDT_update = os.path.isfile(XBL_CONFIG_RAW_ELF)
        if dircet_CDT_update == 0:
            print('ERROR: unable to disassemble xbl config')
            return prc.returncode
        else:
            print('CDT will be directly added into xbl config elf')

    # Set up DTS/DTB paths for use inside the per-board loop
    dts_file = None
    base_dtb_name = None
    dtcBin = None

    # Initialize default frequencies from fallback constants
    default_ddr3_freq = DEFAULT_DDR3_BOOT_FREQ
    default_ddr4_freq = DEFAULT_DDR4_BOOT_FREQ
    default_ddr5_freq = DEFAULT_DDR5_BOOT_FREQ

    if dircet_CDT_update == 0:
        dtcBin = os.path.join(dtcDir, "dtc")

        if ARCH_NAME == "ipq5424" and not genqccfg:
            dts_file = cdir + "/ipq5424/xbl_config/xbl-cust-marina-1.0.dts"
            base_dtb_name = "xbl-cust-marina-1.0.dtb"
        else:
            dts_file = cdir + "/" + ARCH_NAME + "/qc_config/qc-cust-" + ARCH_NAME + "-1.0.dts"
            base_dtb_name = "qc-cust-" + ARCH_NAME + "-1.0.dtb"

        if dts_file and not os.path.isfile(dts_file):
            print('ERROR: DTS file not found: {0}'.format(dts_file))
            return -1

        # Parse default DDR boot frequencies from the base DTS
        if dts_file:
            dts_defaults = parse_default_freqs_from_dts(dts_file)
            default_ddr3_freq = dts_defaults.get('ddr3_boot_freq', DEFAULT_DDR3_BOOT_FREQ)
            default_ddr4_freq = dts_defaults.get('ddr4_boot_freq', DEFAULT_DDR4_BOOT_FREQ)
            default_ddr5_freq = dts_defaults.get('ddr5_boot_freq', DEFAULT_DDR5_BOOT_FREQ)
            print("Default DDR frequencies from DTS: DDR3={0} KHz, DDR4={1} KHz, DDR5={2} KHz".format(
                default_ddr3_freq, default_ddr4_freq, default_ddr5_freq))

        # For ipq5424 non-genqccfg mode, generate a single DTB once (not per-RDP)
        if ARCH_NAME == "ipq5424" and not genqccfg:
            dtb_file = srcDir + "/" + base_dtb_name
            cmd = [dtcBin, '-@', '-O', 'dtb', '-o', dtb_file, dts_file]
            print(cmd)
            prc = subprocess.Popen(cmd, cwd=cdir)
            prc.wait()
            if prc.returncode != 0:
                print('ERROR: unable to generate dtb')
                return prc.returncode

    if ARCH_NAME == "ipq5424" and not genqccfg:
        config_name = "xblconfig-"
    else:
        config_name = "qcconfig-"

    if ARCH_NAME != "ipq806x":
        entries = root.findall("./data[@type='MACH_ID_BOARD_MAP']/entry")

        for entry in entries:
            memory = None
            machid = entry.find(".//machid")
            board = entry.find(".//board")
            if memory_profile != "default":
                memory = entry.find(".//memory_" + memory_profile)

            if memory == None:
                memory = entry.find(".//memory")

            # Gracefully skip RDP entries that don't have default profile
            if memory == None:
                print("WARNING: Skipping RDP entry %s - no memory configuration found for profile '%s'" % (board.text, memory_profile))
                continue

            if ARCH_NAME == "ipq9650":
                if memory_profile == '2048' or memory_profile == '1024' or memory_profile == '512':
                    name_suffix =  board.text + "_" + memory.text + "_LM" + memory_profile
                else:
                    name_suffix =  board.text + "_" + memory.text
            else:
                if memory_profile == '128' or memory_profile == '256' or memory_profile == '512':
                    name_suffix =  board.text + "_" + memory.text + "_LM" + memory_profile
                else:
                    name_suffix =  board.text + "_" + memory.text

            cdt_bin =  "cdt-" + name_suffix + ".bin"

            if dircet_CDT_update == 0:
                # For genqccfg mode, generate RDP-specific DTS and DTB per board
                if genqccfg:
                    # Determine DDR type from memory string
                    mem_text = memory.text.upper()
                    if "DDR4" in mem_text:
                        ddr_type = "DDR4"
                        freq_elem = entry.find(".//ddr4_boot_freq")
                        if freq_elem is None:
                            print("WARNING: mem_type is DDR4 but ddr4_boot_freq is not present in config.xml for board '{0}'. Using default {1} KHz.".format(board.text, default_ddr4_freq))
                        boot_freq = int(freq_elem.text) if freq_elem is not None else default_ddr4_freq
                    elif "DDR3" in mem_text:
                        ddr_type = "DDR3"
                        freq_elem = entry.find(".//ddr3_boot_freq")
                        if freq_elem is None:
                            print("WARNING: mem_type is DDR3 but ddr3_boot_freq is not present in config.xml for board '{0}'. Using default {1} KHz.".format(board.text, default_ddr3_freq))
                        boot_freq = int(freq_elem.text) if freq_elem is not None else default_ddr3_freq
                    elif "DDR5" in mem_text:
                        ddr_type = "DDR5"
                        freq_elem = entry.find(".//ddr5_boot_freq")
                        if freq_elem is None:
                            print("WARNING: mem_type is DDR5 but ddr5_boot_freq is not present in config.xml for board '{0}'. Using default {1} KHz.".format(board.text, default_ddr5_freq))
                        boot_freq = int(freq_elem.text) if freq_elem is not None else default_ddr5_freq
                    else:
                        ddr_type = "DDR4"
                        boot_freq = default_ddr4_freq

                    print("Generating RDP-specific DTS for {0} ({1}={2} KHz)".format(
                        board.text, ddr_type, boot_freq))

                    rdp_dts_path, rdp_dts_name = generate_rdp_dts(
                        dts_file, board.text, ddr_type, boot_freq, srcDir, ARCH_NAME)
                    rdp_dtb_name = rdp_dts_name.replace('.dts', '.dtb')
                    rdp_dtb_path = os.path.join(srcDir, rdp_dtb_name)

                    cmd = [dtcBin, '-@', '-O', 'dtb', '-o', rdp_dtb_path, rdp_dts_path]
                    print(cmd)
                    prc = subprocess.Popen(cmd, cwd=cdir)
                    prc.wait()
                    if prc.returncode != 0:
                        print('ERROR: unable to generate dtb for {0}'.format(board.text))
                        return prc.returncode

                # edit the cdt name and (for genqccfg) the dtb name in json
                with open(xblconfig_json, 'r') as file:
                    # Parse JSON data
                    Data = json.load(file)

                Temp_Data=Data['CFGL']
                for key,value in Temp_Data.items():
                    if isinstance(value, dict):
                        for key1,value1 in value.items():
                            if key1 == "config_name":
                                if value1 == "/cdt.bin":
                                    value["file_name"] = cdt_bin
                            elif key1 == "file_name" and genqccfg:
                                if value1 == base_dtb_name:
                                    value["file_name"] = rdp_dtb_name

                outfile_json = os.path.join(srcDir, "create_xbl_config-" + name_suffix + ".json")
                with open(outfile_json, "w") as outfile:
                    json.dump(Data, outfile)

                #copy the cdt bin
                shutil.copy2(cdir+'/'+cdt_bin, srcDir);

                out_xblconfig = config_name + name_suffix
                outfile_xblconfig = os.path.join(srcDir, out_xblconfig )

                print('Generating xblconfig')
                config = ARCH_CONFIG[ARCH_NAME]
                cmd = [PYTHON_EXECUTABLE, xblconfigtool_gen, '-i', outfile_json, '-fELF', '-o', outfile_xblconfig,
                       '--tools_path', xblconfigtool_path, '--elf-address', config['elf_address'], '-b', srcDir]
                if config['align']:
                    cmd.extend(['--align', config['align']])
                print(cmd)
                prc = subprocess.Popen(cmd, cwd=cdir)
                prc.wait()
                if prc.returncode != 0:
                    print('ERROR: unable to create xbl config')
                    return prc.returncode

                outfile_xblconfig = os.path.join(srcDir,'raw', out_xblconfig + ".elf")
            else:
                out_xblconfig = config_name + name_suffix
                outfile_xblconfig =  cdir + "/" + out_xblconfig + "_raw.elf"
                shutil.copyfile(XBL_CONFIG_RAW_ELF, outfile_xblconfig)
                ret = update_CDT_segment(outfile_xblconfig, cdt_bin)

                if ret < 0:
                    print("CDT segment update failed")
                    return ret

            #elf2mbn conversion
            bootconfig_path = cdir +'/scripts' + '/elftombn.py'
            print("Converting xbconfig elf to mbn using MBN version " + mbn_version + " ...")
            cmd = ['python', bootconfig_path, '-a', ARCH_NAME, '-f', outfile_xblconfig, '-o', cdir + "/" + out_xblconfig + ".elf", '-v', mbn_version, '-s', "37"]
            print(cmd)
            prc = subprocess.Popen(cmd, cwd=cdir)
            prc.wait()
            if prc.returncode != 0:
                print('ERROR: unable to create xbl config')
                return prc.returncode

            os.remove(os.path.join(cdir, out_xblconfig + ".hash"))
            os.remove(os.path.join(cdir, out_xblconfig + "_hash.hd"))
            os.remove(os.path.join(cdir, out_xblconfig + "_phdr.pbn"))
            os.remove(os.path.join(cdir, out_xblconfig + "_combined_hash.mbn"))
            if dircet_CDT_update == 1:
                os.remove(os.path.join(cdir, out_xblconfig + "_raw.elf"))

if __name__ == '__main__':
    main()
