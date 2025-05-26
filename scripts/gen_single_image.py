# ===========================================================================
# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: ISC
# ===========================================================================


import os
import sys
import subprocess
import argparse

def main(target, arch):
		input_dir = os.path.abspath(os.path.join(os.getcwd(), "..", "..", "qsdk", "ipq"))
		output_dir = os.path.join(input_dir, "bin")

		if target == "ipq54xx" and arch == "32":
			commands = [
				f"python {input_dir}/prepareSingleImage.py --arch ipq5424 --fltype nand,emmc,norplusnand,norplusnand-gpt,norplusemmc,norplusemmc-gpt --in {input_dir} --gencdt --genxblcfg --genpart --genmbn",
				f"cp {input_dir}/xbl_sc.elf {input_dir}/xbl_s.melf && cat {input_dir}/tmel-ipq54xx-patch.elf >> {input_dir}/xbl_s.melf",
				f"cp {input_dir}/xbl_sc_flashless.elf {input_dir}/xbl_s_flashless.melf && cat {input_dir}/tmel-ipq54xx-patch.elf >> {input_dir}/xbl_s_flashless.melf",
				f"cp {input_dir}/xbl_sc_devprg.elf {input_dir}/xbl_s_devprg.melf && cat {input_dir}/tmel-ipq54xx-patch.elf >> {input_dir}/xbl_s_devprg.melf",
				f"python {input_dir}/Gen_xbl_nand_elf.py {input_dir}/xbl_s.melf -f NAND_2K -o {input_dir}/nand_elf/",
				f"python {input_dir}/Gen_xbl_nand_elf.py {input_dir}/xbl_s.melf -f NAND_4K -o {input_dir}/nand_elf/",
				f"mv {input_dir}/nand_elf/xbl_nand.elf {input_dir}/xbl_s_nand.melf",
				f"mv {input_dir}/nand_elf/xbl_nand_4K.elf {input_dir}/xbl_s_nand_4K.melf",
				f"python {input_dir}/scripts/pack_v3.py --arch ipq5424 --fltype nand,emmc,norplusnand,norplusnand-gpt,norplusemmc,norplusemmc-gpt --srcPath {input_dir} --inImage {input_dir} --outImage {output_dir}",
				f"python {input_dir}/scripts/pack_v3.py --arch ipq5424 --fltype emmc --srcPath {input_dir} --inImage {input_dir} --outImage {output_dir} --flayout=vendor --img_suffix=vendor",
				f"python {input_dir}/scripts/pack_v3.py --arch ipq5424 --fltype nand,emmc,norplusnand,norplusnand-gpt,norplusemmc,norplusemmc-gpt --srcPath {input_dir} --inImage {input_dir} --outImage {output_dir} --image_type hlos",
				f"python {input_dir}/scripts/pack_v3.py --arch ipq5424 --fltype emmc --srcPath {input_dir} --inImage {input_dir} --outImage {output_dir} --flayout=vendor --img_suffix=vendor --image_type hlos"
			]
		elif target == "ipq54xx" and arch == "64":
			commands = [
				f"python {input_dir}/prepareSingleImage.py --arch ipq5424_64 --fltype nand,emmc,norplusnand,norplusnand-gpt,norplusemmc,norplusemmc-gpt --in {input_dir} --genxblcfg --gencdt --genpart --genmbn",
				f"cp {input_dir}/xbl_sc.elf {input_dir}/xbl_s.melf && cat {input_dir}/tmel-ipq54xx-patch.elf >> {input_dir}/xbl_s.melf",
				f"cp {input_dir}/xbl_sc_flashless.elf {input_dir}/xbl_s_flashless.melf && cat {input_dir}/tmel-ipq54xx-patch.elf >> {input_dir}/xbl_s_flashless.melf",
				f"cp {input_dir}/xbl_sc_devprg.elf {input_dir}/xbl_s_devprg.melf && cat {input_dir}/tmel-ipq54xx-patch.elf >> {input_dir}/xbl_s_devprg.melf",
				f"python {input_dir}/Gen_xbl_nand_elf.py {input_dir}/xbl_s.melf -f NAND_2K -o {input_dir}/nand_elf/",
				f"python {input_dir}/Gen_xbl_nand_elf.py {input_dir}/xbl_s.melf -f NAND_4K -o {input_dir}/nand_elf/",
				f"mv {input_dir}/nand_elf/xbl_nand.elf {input_dir}/xbl_s_nand.melf",
				f"mv {input_dir}/nand_elf/xbl_nand_4K.elf {input_dir}/xbl_s_nand_4K.melf",
				f"python {input_dir}/scripts/pack_v3.py --arch ipq5424_64 --fltype nand,emmc,norplusnand,norplusnand-gpt,norplusemmc,norplusemmc-gpt --srcPath {input_dir} --inImage {input_dir} --outImage {output_dir}",
				f"python {input_dir}/scripts/pack_v3.py --arch ipq5424_64 --fltype emmc --srcPath {input_dir} --inImage {input_dir} --outImage {output_dir} --flayout=vendor --img_suffix=vendor",
				f"python {input_dir}/scripts/pack_v3.py --arch ipq5424_64 --fltype nand,emmc,norplusnand,norplusnand-gpt,norplusemmc,norplusemmc-gpt --srcPath {input_dir} --inImage {input_dir} --outImage {output_dir} --image_type hlos",
				f"python {input_dir}/scripts/pack_v3.py --arch ipq5424_64 --fltype emmc --srcPath {input_dir} --inImage {input_dir} --outImage {output_dir} --flayout=vendor --img_suffix=vendor --image_type hlos"
			]
		elif target == "ipq53xx" and arch == "32":
			commands = [
				f"sed -i -- 's#wifi_fw_ipq5332_qcn9224_v2_qcn6432_qcn9160_squashfs.img#wifi_fw_ipq5332_qcn6432_squashfs.img#g' {input_dir}/ipq5332/config.xml",
				f"sed -i -- 's#wifi_fw_ipq5332_qcn6432cs_qcn9160_squashfs.img#wifi_fw_ipq5332_qcn6432_squashfs.img#g' {input_dir}/ipq5332/config.xml",
				f"sed -i -- 's#wifi_fw_ipq5332_qcn9224_v2_qcn9160_squashfs.img#wifi_fw_ipq5332_qcn9224_v2_single_dualmac_squashfs.img#g' {input_dir}/ipq5332/config.xml",
				f"python {input_dir}/prepareSingleImage.py --arch ipq5332 --fltype emmc,nand,norplusemmc,norplusnand --in {input_dir}/ --gencdt --genmbn --genpart --genbootconf",
				f"python {input_dir}/scripts/pack_v3.py --arch ipq5332 --fltype emmc,nand,norplusemmc,norplusnand --srcPath {input_dir} --inImage {input_dir} --outImage {output_dir}",
				f"python {input_dir}/scripts/pack_v3.py --arch ipq5332 --fltype emmc,nand,norplusemmc,norplusnand --srcPath {input_dir} --inImage {input_dir} --outImage {output_dir} --image_type hlos"
			]
		elif target == "ipq53xx" and arch == "64":
			commands = [
				f"sed -i -- 's#wifi_fw_ipq5332_qcn9224_v2_qcn6432_qcn9160_squashfs.img#wifi_fw_ipq5332_qcn6432_squashfs.img#g' {input_dir}/ipq5332/config.xml",
                f"sed -i -- 's#wifi_fw_ipq5332_qcn6432cs_qcn9160_squashfs.img#wifi_fw_ipq5332_qcn6432_squashfs.img#g' {input_dir}/ipq5332/config.xml",
                f"sed -i -- 's#wifi_fw_ipq5332_qcn9224_v2_qcn9160_squashfs.img#wifi_fw_ipq5332_qcn9224_v2_single_dualmac_squashfs.img#g' {input_dir}/ipq5332/config.xml",
				f"python {input_dir}/prepareSingleImage.py --arch ipq5332_64 --fltype emmc,nand,norplusemmc,norplusnand --in {input_dir}/ --gencdt --genmbn --genpart --genbootconf",
				f"python {input_dir}/scripts/pack_v3.py --arch ipq5332_64 --fltype emmc,nand,norplusemmc,norplusnand --srcPath {input_dir} --inImage {input_dir} --outImage {output_dir}",
				f"python {input_dir}/scripts/pack_v3.py --arch ipq5332_64 --fltype emmc,nand,norplusemmc,norplusnand --srcPath {input_dir} --inImage {input_dir} --outImage {output_dir} --image_type hlos"
			]
		elif target == "ipq95xx" and arch == "32":
			commands = [
				f"unsquashfs -d {input_dir}/tmp_final_v2_1 {input_dir}/wifi_fw_ipq9574_squashfs.img && unsquashfs -d {input_dir}/tmp_wkk_v2_1 {input_dir}/wifi_fw_qcn9224_v2_dualmac_squashfs.img",
                f"cp -rf {input_dir}/tmp_wkk_v2_1/* {input_dir}/tmp_final_v2_1",
                f"{input_dir}/mksquashfs4 {input_dir}/tmp_final_v2_1 {input_dir}/wifi_fw_ipq9574_qcn9224_v2_dualmac_squashfs.img -noappend -root-owned -comp xz -Xpreset 9 -Xe -Xlc 0 -Xlp 2 -Xpb 2 -Xbcj arm -b 256k -processors 1",
                f"unsquashfs -d {input_dir}/tmp_final_v2_2 {input_dir}/wifi_fw_ipq9574_qcn9000_squashfs.img && unsquashfs -d {input_dir}/tmp_wkk_v2_2 {input_dir}/wifi_fw_qcn9224_v2_squashfs.img",
                f"cp -rf {input_dir}/tmp_wkk_v2_2/* {input_dir}/tmp_final_v2_2",
                f"{input_dir}/mksquashfs4 {input_dir}/tmp_final_v2_2 {input_dir}/wifi_fw_ipq9574_qcn9000_qcn9224_v2_squashfs.img -noappend -root-owned -comp xz -Xpreset 9 -Xe -Xlc 0 -Xlp 2 -Xpb 2 -Xbcj arm -b 256k -processors 1",
				f"python {input_dir}/prepareSingleImage.py --arch ipq9574 --fltype nand,norplusnand,emmc,norplusemmc --in {input_dir} --gencdt --genbootconf --genpart --genmbn",
				f"python {input_dir}/scripts/pack.py --arch ipq9574 --fltype nand,norplusnand,emmc,norplusemmc  --srcPath {input_dir} --inImage {input_dir} --outImage {output_dir} --multi_wifi_fw",
				f"python {input_dir}/scripts/pack.py --arch ipq9574 --fltype nand,norplusnand,emmc,norplusemmc  --srcPath {input_dir} --inImage {input_dir} --outImage {output_dir} --image_type hlos --multi_wifi_fw"
			]
		elif target == "ipq95xx" and arch == "64":
			commands = [
				f"unsquashfs -d {input_dir}/tmp_final_v2_1 {input_dir}/wifi_fw_ipq9574_squashfs.img && unsquashfs -d {input_dir}/tmp_wkk_v2_1 {input_dir}/wifi_fw_qcn9224_v2_dualmac_squashfs.img",
				f"cp -rf {input_dir}/tmp_wkk_v2_1/* {input_dir}/tmp_final_v2_1",
				f"{input_dir}/mksquashfs4 {input_dir}/tmp_final_v2_1 {input_dir}/wifi_fw_ipq9574_qcn9224_v2_dualmac_squashfs.img -noappend -root-owned -comp xz -Xpreset 9 -Xe -Xlc 0 -Xlp 2 -Xpb 2 -Xbcj arm -b 256k -processors 1",
				f"unsquashfs -d {input_dir}/tmp_final_v2_2 {input_dir}/wifi_fw_ipq9574_qcn9000_squashfs.img && unsquashfs -d {input_dir}/tmp_wkk_v2_2 {input_dir}/wifi_fw_qcn9224_v2_squashfs.img",
				f"cp -rf {input_dir}/tmp_wkk_v2_2/* {input_dir}/tmp_final_v2_2",
				f"{input_dir}/mksquashfs4 {input_dir}/tmp_final_v2_2 {input_dir}/wifi_fw_ipq9574_qcn9000_qcn9224_v2_squashfs.img -noappend -root-owned -comp xz -Xpreset 9 -Xe -Xlc 0 -Xlp 2 -Xpb 2 -Xbcj arm -b 256k -processors 1",
				f"python {input_dir}/prepareSingleImage.py --arch ipq9574_64 --fltype nand,norplusnand,emmc,norplusemmc --in {input_dir} --gencdt --genbootconf --genpart --genmbn",
				f"python {input_dir}/scripts/pack.py --arch ipq9574_64 --fltype nand,norplusnand,emmc,norplusemmc  --srcPath {input_dir} --inImage {input_dir} --outImage {output_dir} --multi_wifi_fw",
				f"python {input_dir}/scripts/pack.py --arch ipq9574_64 --fltype nand,norplusnand,emmc,norplusemmc  --srcPath {input_dir} --inImage {input_dir} --outImage {output_dir} --image_type hlos --multi_wifi_fw"
			]
		else:
			print(f"Unsupported target ({target}) or architecture ({arch}).")
			sys.exit(1)

		for command in commands:
			subprocess.run(command, shell=True, check=True)

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Generate single image")
	parser.add_argument("target", help="Target SoC")
	parser.add_argument("arch", help="Architecture")
	args = parser.parse_args()

	main(args.target, args.arch)
