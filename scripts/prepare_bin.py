# ===========================================================================
# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: ISC
# ===========================================================================


import os
import sys
import subprocess
import argparse

# Mapping of SoC names to their respective download QART URLs
base_url = "https://qartifactory-edge.qualcomm.com/artifactory/qsc_releases/software/chip/qca-networking-2025-spf-13-0/qca-networking-2025-spf-13-0-qca-oem-qartifact/"
download_links = {
	"ipq95xx": [
		"{version}/tz-win-1-0/trustzone_images/build/ms/bin/OAPAANAA/devcfg.mbn",
		"{version}/tz-win-1-0/trustzone_images/build/ms/bin/OAPAANAA/apdp.mbn",
		"{version}/tz-win-1-0/trustzone_images/build/ms/bin/OAPAANAA/tz.mbn",
		"{version}/win-atf-13-0/atf_proc/out/proprietary/qtiseclib/output/ipq95xx/release/libqtisec.a",
		"{version}/tmel-wns-2-0/tmel-ipq95xx-firmware.elf",
		"{version}/boot-xf-0-3-1-2/boot_images/QcomPkg/IPQ9574Pkg/Tools/bootconfig_tool",
		"{version}/boot-xf-0-3-1-2/boot_images/QcomPkg/IPQ9574Pkg/Tools/partition_tool",
		"{version}/boot-xf-0-3-1-2/boot_images/QcomPkg/IPQ9574Pkg/Bin/9574/LA/RELEASE/sign/default/sbl1/xbl_nand.elf",
		"{version}/boot-xf-0-3-1-2/boot_images/QcomPkg/IPQ9574Pkg/Bin/9574/LA/RELEASE/sign/default/sbl1/xbl.elf",
		"{version}/rpm-bf-2-4-1/IPQ9574/rpm_proc/build/ms/bin/9574/rpm.mbn",
		"{version}/boot-xf-0-3-1-2/boot_images/QcomPkg/Tools/storage/fh_loader/QSaharaServer.exe",
		"{version}/wlan-hk-2-13-0-1/wlan_proc/build/ms/bin/9574-wlanfw-eval/FW_IMAGES/wifi_fw_ipq9574_qcn9000_squashfs.img",
		"{version}/wlan-hk-2-13-0-1/wlan_proc/build/ms/bin/9574-wlanfw-eval/FW_IMAGES/wifi_fw_ipq9574_squashfs.img",
		"{version}/wlan-wbe-1-5/wlan_proc/build/ms/bin/9224-wlanfw-eval_v2/upstream/wifi_fw_qcn9224_v2_squashfs",
		"{version}/wlan-wbe-1-5/wlan_proc/build/ms/bin/9224-wlanfw-single_dualmac_v2/upstream/wifi_fw_qcn9224_v2_dualmac_squashfs"
	],
	"ipq53xx": [
		"{version}/tz-win-1-0/trustzone_images/build/ms/bin/MAPAANAA/devcfg.mbn",
		"{version}/tz-win-1-0/trustzone_images/build/ms/bin/MAPAANAA/tz.mbn",
		"{version}/boot-xf-0-3-1-2/boot_images/QcomPkg/IPQ5332Pkg/Tools/bootconfig_tool",
		"{version}/boot-xf-0-3-1-2/boot_images/QcomPkg/IPQ5332Pkg/Tools/partition_tool",
		"{version}/boot-xf-0-3-1-2/boot_images/QcomPkg/IPQ5332Pkg/Bin/5332/LA/RELEASE/NOR/sign/default/sbl1/xbl_nor.elf",
		"{version}/boot-xf-0-3-1-2/boot_images/QcomPkg/IPQ5332Pkg/Bin/5332/LA/RELEASE/EMMC/sign/default/sbl1/xbl_emmc.elf",
		"{version}/boot-xf-0-3-1-2/boot_images/QcomPkg/IPQ5332Pkg/Bin/5332/LA/RELEASE/NAND/sign/default/sbl1/xbl_nand.elf",
		"{version}/boot-xf-0-3-1-2/boot_images/QcomPkg/IPQ5332Pkg/Bin/5332/LA/RELEASE/NAND/sign/default/sbl1/xbl_nand_4K.elf",
		"{version}/boot-xf-0-3-1-2/boot_images/QcomPkg/IPQ5332Pkg/Bin/5332/LA/RELEASE/NAND/sign/default/sbl1/xbl_nand_noPreamble.elf",
		"{version}/boot-xf-0-3-1-2/boot_images/QcomPkg/IPQ5332Pkg/Bin/5332/LA/RELEASE/TINY_NOR/sign/default/sbl1/xbl_tiny_nor.elf",
		"{version}/boot-xf-0-3-1-2/boot_images/QcomPkg/IPQ5332Pkg/Bin/5332/LA/RELEASE/FLASHLESS/sign/default/sbl1/xbl_flashless.elf",
		"{version}/boot-xf-0-3-1-2/boot_images/QcomPkg/IPQ5332Pkg/Bin/5332/LA/RELEASE/LM256/NOR/sign/default/sbl1/xbl_nor_LM256.elf",
		"{version}/boot-xf-0-3-1-2/boot_images/QcomPkg/IPQ5332Pkg/Bin/5332/LA/RELEASE/LM256/NAND/sign/default/sbl1/xbl_nand_noPreamble_LM256.elf",
		"{version}/boot-xf-0-3-1-2/boot_images/QcomPkg/IPQ5332Pkg/Bin/5332/LA/RELEASE/LM256/NAND/sign/default/sbl1/xbl_nand_LM256.elf",
		"{version}/boot-xf-0-3-1-2/boot_images/QcomPkg/IPQ5332Pkg/Bin/5332/LA/RELEASE/LM256/NAND/sign/default/sbl1/xbl_nand_4K_LM256.elf",
		"{version}/boot-xf-0-3-1-2/boot_images/QcomPkg/IPQ5332Pkg/Bin/5332/LA/RELEASE/LM256/EMMC/sign/default/sbl1/xbl_emmc_LM256.elf",
		"{version}/boot-xf-0-3-1-2/boot_images/QcomPkg/IPQ5332Pkg/Bin/5332/LA/RELEASE/LM256/TINY_NOR/sign/default/sbl1/xbl_tiny_nor_LM256.elf",
		"{version}/boot-xf-0-3-1-2/boot_images/QcomPkg/IPQ5332Pkg/Bin/5332/LA/RELEASE/LM256/FLASHLESS/sign/default/sbl1/xbl_flashless_LM256.elf",
		"{version}/tmel-wns-2-1/tmel-ipq53xx-patch.elf",
		"{version}/win-atf-13-0/atf_proc/out/proprietary/secboot_lib/output/ipq53xx/release/libsecboot.a",
		"{version}/win-atf-13-0/atf_proc/out/proprietary/qtiseclib/output/ipq53xx/release/libqtisec.a",
		"{version}/boot.xf.0.3.1.2/boot_images/QcomPkg/Tools/storage/fh_loader/QSaharaServer.exe",
		"{version}/wlan-wbe-1-5/wlan_proc/build/ms/bin/5332-wlan_fw2-mia_peb_eval/upstream/FW_IMAGES/wifi_fw_ipq5332_qcn6432_squashfs.img",
		"{version}/wlan-wbe-1-5/wlan_proc/build/ms/bin/5332-wlan_fw2-mia_peb_eval/upstream/FW_IMAGES/wifi_fw_ipq5332_qcn9224_v2_qcn6432_squashfs.img",
		"{version}/wlan-wbe-1-5/wlan_proc/build/ms/bin/5332-wlan_fw2-mia_peb_peb_eval_cs/upstream/FW_IMAGES/wifi_fw_ipq5332_qcn6432cs_squashfs.img",
		"{version}/wlan-wbe-1-5/wlan_proc/build/ms/bin/5332-wlan_fw3-mia_peb_peb_york_eval_cs/upstream/FW_IMAGES/wifi_fw_ipq5332_qcn6432cs_qcn9160_squashfs.img",
		"{version}/wlan-wbe-1-5/wlan_proc/build/ms/bin/5332-wlan_fw3-mia_peb_york_eval/upstream/FW_IMAGES/wifi_fw_ipq5332_qcn9224_v2_qcn6432_qcn9160_squashfs.img",
		"{version}/wlan-wbe-1-5/wlan_proc/build/ms/bin/5332-wlanfw-eval/upstream/FW_IMAGES/wifi_fw_ipq5332_qcn9224_v2_single_dualmac_squashfs.img",
		"{version}/wlan-wbe-1-5/wlan_proc/build/ms/bin/5332-wlanfw-eval/upstream/FW_IMAGES/wifi_fw_ipq5332_qcn9224_v2_squashfs.img",
		"{version}/wlan-wbe-1-5/wlan_proc/build/ms/bin/5332-wlanfw-eval/upstream/FW_IMAGES/wifi_fw_ipq5332_squashfs.img",
		"{version}/wlan-wbe-1-5/wlan_proc/build/ms/bin/5332-wlanfw2-miami_york_eval/upstream/FW_IMAGES/wifi_fw_ipq5332_qcn9224_v2_qcn9160_squashfs.img"
	],
	"ipq54xx": [
		"{version}/tz-win_wc-1-0/trustzone_images/build/ms/bin/MAPAANAA/devcfg.mbn",
		"{version}/tz-win_wc-1-0/trustzone_images/build/ms/bin/MAPAANAA/tz.mbn",
		"{version}/win-atf_wc-13-0/atf_proc/out/proprietary/qtiseclib/output/ipq54xx/release/libqtisec.a",
		"{version}/tmel-wns-2-2/tmel-ipq54xx-patch.elf",
		"{version}/boot-mxf-2-3-1/boot_images/boot/QcomPkg/SocPkg/Marina/Bin_ext/LE/QC_sign/xbl_sc.elf",
		"{version}/boot-mxf-2-3-1/boot_images/boot/QcomPkg/SocPkg/Marina/Bin_ext/MN/QC_sign/xbl_sc_devprg.elf",
		"{version}/boot-mxf-2-3-1/boot_images/boot/QcomPkg/SocPkg/Marina/Bin_ext/MN/QC_sign/xbl_sc_flashless.elf",
		"{version}/boot-mxf-2-3-1/boot_images/boot/Settings/Soc/Marina/xbl-cust-marina-1.0.dts",
		"{version}/boot-mxf-2-3-1/boot_images/boot_tools/partition_tool/partition_tool",
		"{version}/boot-mxf-2-3-1/boot_images/boot_tools/create_multielf.py",
		"{version}/boot-mxf-2-3-1/boot_images/boot_tools/Gen_xbl_nand_elf.py",
		"{version}/boot-mxf-2-3-1/boot_images/Build/MarinaMN/xblconfig/auto_gen/elf_files/create_cli/xbl_config_raw.elf",
		"{version}/boot-mxf-2-3-1/boot_images/boot_tools/QSaharaServer/QSaharaServer.exe",
		"{version}/wlan-wbe-1-5/wlan_proc/build/ms/bin/5424-wlanfw-eval/upstream/FW_IMAGES/wifi_fw_ipq5424_qcn9224_v2_squashfs.img"
	]
}

def main():
	if len(sys.argv) != 3:
		print("Usage: python prepare_binaries.py <target_soc> <version_string>")
		sys.exit(1)

	target_soc = sys.argv[1]
	version_string = sys.argv[2]
	if target_soc not in download_links:
		print(f"Unsupported SoC: {target_soc}")
		sys.exit(1)

	target_dir = os.path.abspath(os.path.join(os.getcwd(), "..", "..", "qsdk", "ipq"))
	os.makedirs(target_dir, exist_ok=True)
	os.chdir(target_dir)

	print(f"Downloading binaries for {target_soc} into {target_dir}...\n")

	for url_template in download_links[target_soc]:
		url = base_url + url_template.format(version=version_string)
		filename = url.split("/")[-1]
		try:
			subprocess.run(["wget", url], check=True)
			if os.path.exists(filename):
				with open(filename, 'rb') as f:
					if b"<html" in f.read(1024).lower():
						print(f"Warning: {filename} appears to be an HTML page. Check authentication or URL.")
		except subprocess.CalledProcessError:
			print(f"Failed to download: {url}")

	print("\nDownload complete.")

if __name__ == "__main__":
	main()
