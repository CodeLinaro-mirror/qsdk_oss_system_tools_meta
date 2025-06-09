# ===========================================================================
# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: ISC
# ===========================================================================

try: input = raw_input
except NameError: raw_input = input

import argparse
import os
import subprocess
import time
import shutil

def get_user_input():
	boot_build_path = raw_input("Enter the IPQ Folder Path: ")

	target_types = ["IPQ95xx", "IPQ53xx", "IPQ54xx"]
	print("Choose the TargetType from the following options:")
	for i, target in enumerate(target_types, 1):
		print("%d. %s" % (i, target))

	target_type_index = int(raw_input("Enter the number corresponding to your choice: ")) - 1
	target_type = target_types[target_type_index]

	board_type = None
	if target_type == "IPQ95xx":
		board_types = ["RDP417/AP.AL01-C1", "RDP418/AP.AL02-C1", "RDP418-EMMC/AP.AL02-C2", "RDP437/AP.AL02-C3", "RDP433/AP.AL02-C4", "AP.AL02-C5", "RDP449/AP.AL02-C6", "RDP433-EMMC/AP.AL02-C7", "RDP453/AP.AL02-C8", "RDP454/AP.AL02-C9", "AP.AL02-C10", "RDP455-C11/AP.AL02-C11", "RDP455-C12/AP.AL02-C12", "RDP459/AP.AL02-C13", "AP.AL02-C14", "RDP457/AP.AL02-C15", "RDP456/AP.AL02-C16", "RDP469/AP.AL02-C17", "AP.AL02-C18", "RDP461/AP.AL02-C19", "RDP467/AP.AL02-C20", "AP.AL03-C1", "RDP458/AP.AL03-C2", "RDP475/AP.AL05", "RDP475-QCA81XX/AP.AL05-QCA81XX", "RDP475-QCA81XX-I2C/AP.AL05-QCA81XX-I2C", "RDP476/AP.AL06", "DB.AL01-C1", "DB.AL01-C2", "DB.AL01-C3", "DB.AL02-C1", "DB.AL02-C2", "DB.AL02-C3"]
	elif target_type == "IPQ53xx":
		board_types = ["RDP441/AP-MI01.2", "RDP441-QCA81XX/AP-MI01.2-QCA81XX", "RDP441-QCA81XX-I2C/AP-MI01.2-QCA81XX-I2C", "RDP484/AP-MI01.2-C2", "RDP472/AP-MI01.2-QCN9160-C1", "RDP442​/AP-MI01.3", "RDP477​/AP-MI01.3-C2", "RDP486​/AP-MI01.3-C3", "RDP477-256M/AP-MI01.3-C4", "RDP444/AP-MI01.4", "RDP468/AP-MI01.6 ", "RDP473/AP-MI01.7", "RDP474/AP-MI01.9", "RDP479/AP-MI01.12", "RDP480/AP-MI01.13", "RDP481/AP-MI01.14", "RDP447/AP-MI03.1", "RDP446/AP-MI04.1", "RDP478/AP-MI04.1-C2", "RDP478-256M/AP-MI04.1-C3", "RDP483/AP-MI04.3", "TB-MI03.1", "TB-MI05.1", "DB-MI01.1", "DB-MI02.1", "DB-MI03.1"]
	elif target_type == "IPQ54xx":
		board_types = ["RDP464/AP-MR01.1", "RDP464-C2/AP-MR01.1-C2", "RDP464-C3/AP-MR01.1-C3", "RDP466/AP-MR02.1", "RDP466-C2/AP-MR02.1-C2", "RDP466-C3/AP-MR02.1-C3", "RDP466-RFFE/AP-MR02.1-RFFE", "RDP485/AP-MR02.2", "RDP485-C2/AP-MR02.2-C2", "RDP485-C3/AP-MR02.2-C3", "RDP485-RFFE/AP-MR02.2-RFFE", "RDP485-RFFE-C2/AP-MR02.2-RFFE-C2", "RDP496/AP-MR02.3", "RDP487/AP-MR03.1", "DB-MR01.1"]

	port_num = raw_input("Enter the port number: ")

	if board_types:
		print("Choose the BoardType from the following options:")
		for i, board in enumerate(board_types, 1):
			print("%d. %s" % (i, board))

		board_type_index = int(raw_input("Enter the number corresponding to your choice: ")) - 1
		board_type = board_types[board_type_index]

	flash_types = ["NAND", "NORPLUSNAND", "EMMC", "NORPLUSEMMC"]
	print("Choose the FlashType from the following options:")
	for i, flash in enumerate(flash_types, 1):
		print("%d. %s" % (i, flash))

	flash_type_index = int(raw_input("Enter the number corresponding to your choice: ")) - 1
	flash_type = flash_types[flash_type_index]

	return boot_build_path, target_type, board_type, flash_type, port_num

def get_cdtbin_file(boot_build_path, board_type, target_type):
	cdtbin_file = None
	board_file_map = {
		"RDP417/AP.AL01-C1": ["cdt-AP-AL01-C1_256M32_DDR3.bin", "cdt-AP-AL01-C1_256M32_DDR3_LM512.bin"],
		"RDP418/AP.AL02-C1": ["cdt-AP-AL02-C1_256M32_DDR4.bin", "cdt-AP-AL02-C1_256M32_DDR4_LM512.bin"],
		"RDP418-EMMC/AP.AL02-C2": ["cdt-AP-AL02-C2_256M32_DDR4.bin", "cdt-AP-AL02-C2_256M32_DDR4_LM512.bin"],
		"RDP437/AP.AL02-C3": ["cdt-AP-AL02-C3_256M32_DDR4.bin", "cdt-AP-AL02-C3_256M32_DDR4_LM512.bin"],
		"RDP433/AP.AL02-C4": ["cdt-AP-AL02-C4_256M32_DDR4.bin", "cdt-AP-AL02-C4_256M32_DDR4_LM512.bin"],
		"AP.AL02-C5": ["cdt-AP-AL02-C5_256M32_DDR4.bin", "cdt-AP-AL02-C5_256M32_DDR4_LM512.bin"],
		"RDP449/AP.AL02-C6": ["cdt-AP-AL02-C6_256M32_DDR4.bin", "cdt-AP-AL02-C6_256M32_DDR4_LM512.bin"],
		"RDP433-EMMC/AP.AL02-C7": ["cdt-AP-AL02-C7_256M32_DDR4.bin", "cdt-AP-AL02-C7_256M32_DDR4_LM512.bin"],
		"RDP453/AP.AL02-C8": ["cdt-AP-AL02-C8_256M32_DDR4.bin", "cdt-AP-AL02-C8_256M32_DDR4_LM512.bin"],
		"RDP454/AP.AL02-C9": ["cdt-AP-AL02-C9_256M32_DDR4.bin", "cdt-AP-AL02-C9_256M32_DDR4_LM512.bin"],
		"AP.AL02-C10": ["cdt-AP-AL02-C10_256M32_DDR4.bin", "cdt-AP-AL02-C10_256M32_DDR4_LM512.bin"],
		"RDP455-C11/AP.AL02-C11": ["cdt-AP-AL02-C11_512M32_DDR4.bin", "cdt-AP-AL02-C11_512M32_DDR4_LM512.bin"],
		"RDP455-C12/AP.AL02-C12": ["cdt-AP-AL02-C12_256M32_DDR4.bin", "cdt-AP-AL02-C12_256M32_DDR4_LM512.bin"],
		"RDP459/AP.AL02-C13": ["cdt-AP-AL02-C13_256M32_DDR4.bin", "cdt-AP-AL02-C13_256M32_DDR4_LM512.bin"],
		"AP.AL02-C14": ["cdt-AP-AL02-C14_256M16_DDR4.bin", "cdt-AP-AL02-C14_256M16_DDR4_LM512.bin"],
		"RDP457/AP.AL02-C15": ["cdt-AP-AL02-C15_256M32_DDR4.bin", "cdt-AP-AL02-C15_256M32_DDR4_LM512.bin"],
		"RDP456/AP.AL02-C16": ["cdt-AP-AL02-C16_512M32_DDR4.bin", "cdt-AP-AL02-C16_512M32_DDR4_LM512.bin"],
		"RDP469/AP.AL02-C17": ["cdt-AP-AL02-C17_256M32_DDR4.bin", "cdt-AP-AL02-C17_256M32_DDR4_LM512.bin"],
		"AP.AL02-C18": ["cdt-AP-AL02-C18_256M32_DDR4.bin", "cdt-AP-AL02-C18_256M32_DDR4_LM512.bin"],
		"RDP461/AP.AL02-C19": ["cdt-AP-AL02-C19_256M32_DDR4.bin", "cdt-AP-AL02-C19_256M32_DDR4_LM512.bin"],
		"RDP467/AP.AL02-C20": ["cdt-AP-AL02-C20_512M32_DDR4.bin", "cdt-AP-AL02-C20_512M32_DDR4_LM512.bin"],
		"AP.AL03-C1": ["cdt-AP-AL03-C1_256M32_DDR3.bin", "cdt-AP-AL03-C1_256M32_DDR3_LM512.bin"],
		"RDP458/AP.AL03-C2": ["cdt-AP-AL03-C2_256M32_DDR3.bin", "cdt-AP-AL03-C2_256M32_DDR3_LM512.bin"],
		"RDP475/AP.AL05": ["cdt-AP-AL05_256M32_DDR4.bin", "cdt-AP-AL05_256M32_DDR4_LM512.bin"],
		"RDP475-QCA81XX/AP.AL05-QCA81XX": ["cdt-AP-AL05-QCA81XX_256M32_DDR4.bin", "cdt-AP-AL05-QCA81XX_256M32_DDR4_LM512.bin"],
		"RDP475-QCA81XX-I2C/AP.AL05-QCA81XX-I2C": ["cdt-AP-AL05-QCA81XX-I2C_256M32_DDR4.bin", "cdt-AP-AL05-QCA81XX_256M32-I2C_DDR4_LM512.bin"],
		"RDP476/AP.AL06": ["cdt-AP-AL06_256M32_DDR4.bin", "cdt-AP-AL06_256M32_DDR4_LM512.bin"],
		"DB.AL01-C1": ["cdt-DB-AL01-C1_256M32_DDR3.bin", "cdt-DB-AL01-C1_256M32_DDR3_LM512.bin"],
		"DB.AL01-C2": ["cdt-DB-AL01-C2_256M32_DDR3.bin", "cdt-DB-AL01-C2_256M32_DDR3_LM512.bin"],
		"DB.AL01-C3": ["cdt-DB-AL01-C3_256M32_DDR3.bin", "cdt-DB-AL01-C3_256M32_DDR3_LM512.bin"],
		"DB.AL02-C1": ["cdt-DB-AL02-C1_1024M32_DDR4.bin", "cdt-DB-AL02-C1_1024M32_DDR4_LM512.bin"],
		"DB.AL02-C2": ["cdt-DB-AL02-C2_1024M32_DDR4.bin", "cdt-DB-AL02-C2_1024M32_DDR4_LM512.bin"],
		"DB.AL02-C3": ["cdt-DB-AL02-C3_1024M32_DDR4.bin", "cdt-DB-AL02-C3_1024M32_DDR4_LM512.bin"],
		"RDP441/AP-MI01.2": ["cdt-AP-MI01.2_512M16_DDR4.bin", "cdt-AP-MI01.2_512M16_DDR4_LM512.bin", "cdt-AP-MI01.2_512M16_DDR4_LM256.bin"],
		"RDP441-QCA81XX/AP-MI01.2-QCA81XX": ["cdt-AP-MI01.2-QCA81XX_512M16_DDR4.bin", "cdt-AP-MI01.2-QCA81XX_512M16_DDR4_LM512.bin", "cdt-AP-MI01.2-QCA81XX_512M16_DDR4_LM256.bin"],
		"RDP441-QCA81XX-I2C/AP-MI01.2-QCA81XX-I2C": ["cdt-AP-MI01.2-QCA81XX-I2C_512M16_DDR4.bin", "cdt-AP-MI01.2-QCA81XX-I2C_512M16_DDR4_LM512.bin"],
		"RDP484/AP-MI01.2-C2": ["cdt-AP-MI01.2-C2_512M16_DDR4.bin", "cdt-AP-MI01.2-C2_512M16_DDR4_LM512.bin", "cdt-AP-MI01.2-C2_512M16_DDR4_LM256.bin"],
		"RDP472/AP-MI01.2-QCN9160-C1": ["cdt-AP-MI01.2-QCN9160-C1_512M16_DDR4.bin", "cdt-AP-MI01.2-QCN9160-C1_512M16_DDR4_LM512.bin", "cdt-AP-MI01.2-QCN9160-C1_512M16_DDR4_LM256.bin"],
		"RDP442​/AP-MI01.3": ["cdt-AP-MI01.3_512M16_DDR4.bin", "cdt-AP-MI01.3_512M16_DDR4_LM512.bin", "cdt-AP-MI01.3_512M16_DDR4_LM256.bin"],
		"RDP477​/AP-MI01.3-C2": ["cdt-RDP 442​/AP-MI01.3-C2_256M16_DDR4.bin", "cdt-RDP 442​/AP-MI01.3-C2_256M16_DDR4_LM512.bin", "cdt-RDP 442​/AP-MI01.3-C2_256M16_DDR4_LM256.bin"],
		"RDP486​/AP-MI01.3-C3": ["cdt-RDP 442​/AP-MI01.3-C3_512M16_DDR4.bin", "cdt-RDP 442​/AP-MI01.3-C3_512M16_DDR4_LM512.bin", "cdt-RDP 442​/AP-MI01.3-C3_512M16_DDR4_LM256.bin"],
		"RDP477-256M/AP-MI01.3-C4": ["cdt-RDP 442​/AP-MI01.3-C4_256M16_DDR4.bin", "cdt-RDP 442​/AP-MI01.3-C4_256M16_DDR4_LM512.bin", "cdt-RDP 442​/AP-MI01.3-C4_256M16_DDR4_LM256.bin"],
		"RDP479/AP-MI01.12": ["cdt-AP-RDP479_512M16_DDR4.bin", "cdt-AP-RDP479_512M16_DDR4_LM512.bin", "cdt-AP-RDP479_512M16_DDR4_LM256.bin"],
		"RDP480/AP-MI01.13": ["cdt-AP-MI01.13_512M16_DDR4.bin", "cdt-AP-MI01.13_512M16_DDR4_LM512.bin", "cdt-AP-MI01.13_512M16_DDR4_LM256.bin"],
		"RDP481/AP-MI01.14": ["cdt-AP-RDP481_512M16_DDR4.bin", "cdt-AP-RDP481_512M16_DDR4_LM512.bin", "cdt-AP-RDP481_512M16_DDR4_LM256.bin"],
		"RDP444/AP-MI01.4": ["cdt-AP-MI01.4_256M16_DDR4.bin", "cdt-AP-MI01.4_256M16_DDR4_LM512.bin", "cdt-AP-MI01.4_256M16_DDR4_LM256.bin"],
		"RDP468/AP-MI01.6 ": ["cdt-AP-MI01.6_512M16_DDR4.bin", "cdt-AP-MI01.6_512M16_DDR4_LM512.bin", "cdt-AP-MI01.6_512M16_DDR4_LM256.bin"],
		"RDP473/AP-MI01.7": ["cdt-AP-MI01.7_512M16_DDR4.bin", "cdt-AP-MI01.7_512M16_DDR4_LM512.bin", "cdt-AP-MI01.7_512M16_DDR4_LM256.bin"],
		"RDP474/AP-MI01.9": ["cdt-AP-MI01.9_512M16_DDR4.bin", "cdt-AP-MI01.9_512M16_DDR4_LM512.bin", "cdt-AP-MI01.9_512M16_DDR4_LM256.bin"],
		"RDP447/AP-MI03.1": ["cdt-AP-MI03.1_128M16_DDR3.bin", "cdt-AP-MI03.1_128M16_DDR3_LM512.bin", "cdt-AP-MI03.1_128M16_DDR3_LM256.bin"],
		"RDP446/AP-MI04.1": ["cdt-AP-MI04.1_256M16_NOM_DDR4.bin", "cdt-AP-MI04.1_256M16_NOM_DDR4_LM512.bin", "cdt-AP-MI04.1_256M16_NOM_DDR4_LM256.bin"],
		"RDP478/AP-MI04.1-C2": ["cdt-AP-MI04.1-C2_256M16_NOM_DDR4.bin", "cdt-AP-MI04.1-C2_256M16_NOM_DDR4_LM512.bin", "cdt-AP-MI04.1-C2_256M16_NOM_DDR4_LM256.bin"],
		"RDP478-256M/AP-MI04.1-C3": ["cdt-AP-MI04.1-C3_256M16_NOM_DDR4.bin", "cdt-AP-MI04.1-C3_256M16_NOM_DDR4_LM512.bin", "cdt-AP-MI04.1-C3_256M16_NOM_DDR4_LM256.bin"],
		"RDP483/AP-MI04.3": ["cdt-AP-MI04.3_256M16_NOM_DDR4.bin", "cdt-AP-MI04.3_256M16_NOM_DDR4_LM512.bin", "cdt-AP-MI04.3_256M16_NOM_DDR4_LM256.bin"],
		"TB-MI03.1": ["cdt-TB-MI03.1_256M16_TB_DDR4.bin", "cdt-TB-MI03.1_256M16_TB_DDR4_LM512.bin", "cdt-TB-MI03.1_256M16_TB_DDR4_LM256.bin"],
		"TB-MI05.1": ["cdt-TB-MI05.1_256M16_TB_DDR3.bin", "cdt-TB-MI05.1_256M16_TB_DDR3_LM512.bin", "cdt-TB-MI05.1_256M16_TB_DDR3_LM256.bin"],
		"DB-MI01.1": ["cdt-DB-MI01.1_512M16_DDR4.bin", "cdt-DB-MI01.1_512M16_DDR4_LM512.bin", "cdt-DB-MI01.1_512M16_DDR4_LM256.bin"],
		"DB-MI02.1": ["cdt-DB-MI02.1_128M16_DDR3.bin", "cdt-DB-MI02.1_128M16_DDR3_LM512.bin", "cdt-DB-MI02.1_128M16_DDR3_LM256.bin"],
		"DB-MI03.1": ["cdt-DB-MI03.1_128M16_DDR3.bin", "cdt-DB-MI03.1_128M16_DDR3_LM512.bin", "cdt-DB-MI03.1_128M16_DDR3_LM256.bin"]
	}

	if target_type == "IPQ54xx":
		return None

	if board_type in board_file_map:
		for file_name in board_file_map[board_type]:
			if os.path.isfile(os.path.join(boot_build_path, file_name)):
				cdtbin_file = file_name
				break

	return cdtbin_file

def get_uboot_file(boot_build_path, flash_type, target_type):
	uboot_file = None
	uboot_file_map = {
		"IPQ95xx": {
			"EMMC": [
				"openwrt-ipq9574-ipq95xx_32-mmc32-u-boot.mbn",
				"openwrt-ipq9574-generic-mmc-u-boot.mbn"
			],
			"NORPLUSEMMC": [
				"openwrt-ipq9574-ipq95xx_32-norplusmmc32-u-boot.mbn",
				"openwrt-ipq9574-generic-norplusmmc-u-boot.mbn"
			],
			"NAND": [
				"openwrt-ipq9574-ipq95xx_32-nand32-u-boot.mbn",
				"openwrt-ipq9574-generic-nand-u-boot.mbn"
			],
			"NORPLUSNAND": [
				"openwrt-ipq9574-ipq95xx_32-norplusnand32-u-boot.mbn",
				"openwrt-ipq9574-generic-norplusnand-u-boot.mbn"
			]
		},
		"IPQ53xx": {
			"EMMC": [
				"openwrt-ipq5332-ipq53xx_32-mmc32-u-boot.mbn",
				"openwrt-ipq5332-generic-mmc-u-boot.mbn"
			],
			"NORPLUSEMMC": [
				"openwrt-ipq5332-ipq53xx_32-norplusmmc32-u-boot.mbn",
				"openwrt-ipq5332-generic-norplusmmc-u-boot.mbn"
			],
			"NAND": [
				"openwrt-ipq5332-ipq53xx_32-nand32-u-boot.mbn",
				"openwrt-ipq5332-generic-nand-u-boot.mbn"
			],
			"NORPLUSNAND": [
				"openwrt-ipq5332-ipq53xx_32-norplusnand32-u-boot.mbn",
				"openwrt-ipq5332-generic-norplusnand-u-boot.mbn"
			]
		},
		"IPQ54xx": {
			"EMMC": [
				"openwrt-ipq5424-generic-mmc-u-boot.mbn",
				"openwrt-ipq5424-ipq54xx_32-mmc32-u-boot.mbn"
			],
			"NORPLUSEMMC": [
				"openwrt-ipq5424-generic-norplusmmc-u-boot.mbn",
				"openwrt-ipq5424-ipq54xx_32-norplusmmc32-u-boot.mbn"
			],
			"NAND": [
				"openwrt-ipq5424-generic-nand-u-boot.mbn",
				"openwrt-ipq5424-ipq54xx_32-nand32-u-boot.mbn"
			],
			"NORPLUSNAND": [
				"openwrt-ipq5424-generic-norplusnand-u-boot.mbn",
				"openwrt-ipq5424-ipq54xx_32-norplusnand32-u-boot.mbn"
			]
		}
	}

	if target_type in uboot_file_map and flash_type in uboot_file_map[target_type]:
		for file_name in uboot_file_map[target_type][flash_type]:
			if os.path.isfile(os.path.join(boot_build_path, file_name)):
				uboot_file = file_name
				break
	return uboot_file

def get_xbl_file(boot_build_path, target_type):
	xbl_file_map = {
		"IPQ95xx": "xbl.elf",
		"IPQ53xx": "xbl_flashless.elf",
		"IPQ54xx": "xbl_s_flashless.melf"
	}

	xbl_file = xbl_file_map.get(target_type)
	if xbl_file and os.path.isfile(os.path.join(boot_build_path, xbl_file)):
		return xbl_file
	return None

def prompt_target_type():
	target_types = ["IPQ95xx", "IPQ53xx", "IPQ54xx"]
	print("Choose the TargetType from the following options:")
	for i, target in enumerate(target_types, 1):
		print("%d. %s" % (i, target))
	index = int(input("Enter the number corresponding to your choice: ")) - 1
	return target_types[index]

def prompt_board_type(target_type):
	if target_type == "IPQ95xx":
		board_types = ["RDP417/AP.AL01-C1", "RDP418/AP.AL02-C1", "RDP418-EMMC/AP.AL02-C2", "RDP437/AP.AL02-C3", "RDP433/AP.AL02-C4", "AP.AL02-C5", "RDP449/AP.AL02-C6", "RDP433-EMMC/AP.AL02-C7", "RDP453/AP.AL02-C8", "RDP454/AP.AL02-C9", "AP.AL02-C10", "RDP455-C11/AP.AL02-C11", "RDP455-C12/AP.AL02-C12", "RDP459/AP.AL02-C13", "AP.AL02-C14", "RDP457/AP.AL02-C15", "RDP456/AP.AL02-C16", "RDP469/AP.AL02-C17", "AP.AL02-C18", "RDP461/AP.AL02-C19", "RDP467/AP.AL02-C20", "AP.AL03-C1", "RDP458/AP.AL03-C2", "RDP475/AP.AL05", "RDP475-QCA81XX/AP.AL05-QCA81XX", "RDP475-QCA81XX-I2C/AP.AL05-QCA81XX-I2C", "RDP476/AP.AL06", "DB.AL01-C1", "DB.AL01-C2", "DB.AL01-C3", "DB.AL02-C1", "DB.AL02-C2", "DB.AL02-C3"]
	elif target_type == "IPQ53xx":
		board_types = ["RDP441/AP-MI01.2", "RDP441-QCA81XX/AP-MI01.2-QCA81XX", "RDP441-QCA81XX-I2C/AP-MI01.2-QCA81XX-I2C", "RDP484/AP-MI01.2-C2", "RDP472/AP-MI01.2-QCN9160-C1", "RDP442​/AP-MI01.3", "RDP477​/AP-MI01.3-C2", "RDP486​/AP-MI01.3-C3", "RDP477-256M/AP-MI01.3-C4", "RDP444/AP-MI01.4", "RDP468/AP-MI01.6 ", "RDP473/AP-MI01.7", "RDP474/AP-MI01.9", "RDP479/AP-MI01.12", "RDP480/AP-MI01.13", "RDP481/AP-MI01.14", "RDP447/AP-MI03.1", "RDP446/AP-MI04.1", "RDP478/AP-MI04.1-C2", "RDP478-256M/AP-MI04.1-C3", "RDP483/AP-MI04.3", "TB-MI03.1", "TB-MI05.1", "DB-MI01.1", "DB-MI02.1", "DB-MI03.1"]
	elif target_type == "IPQ54xx":
		board_types = ["RDP464/AP-MR01.1", "RDP464-C2/AP-MR01.1-C2", "RDP464-C3/AP-MR01.1-C3", "RDP466/AP-MR02.1", "RDP466-C2/AP-MR02.1-C2", "RDP466-C3/AP-MR02.1-C3", "RDP466-RFFE/AP-MR02.1-RFFE", "RDP485/AP-MR02.2", "RDP485-C2/AP-MR02.2-C2", "RDP485-C3/AP-MR02.2-C3", "RDP485-RFFE/AP-MR02.2-RFFE", "RDP485-RFFE-C2/AP-MR02.2-RFFE-C2", "RDP496/AP-MR02.3", "RDP487/AP-MR03.1", "DB-MR01.1"]

	print("Choose the BoardType from the following options:")
	for i, board in enumerate(board_types, 1):
		print("%d. %s" % (i, board))
	index = int(input("Enter the number corresponding to your choice: ")) - 1
	return board_types[index]

def prompt_flash_type():
	flash_types = ["NAND", "NORPLUSNAND", "EMMC", "NORPLUSEMMC"]
	print("Choose the FlashType from the following options:")
	for i, flash in enumerate(flash_types, 1):
		print("%d. %s" % (i, flash))
	index = int(input("Enter the number corresponding to your choice: ")) - 1
	return flash_types[index]

def get_xblconfig_file(boot_build_path, board_type):
	xblconfig_file = None
	board_file_map = {
		"RDP464/AP-MR01.1": [
			"xblconfig-AP-MR01.1_512M32_DDR4.elf",
			"xblconfig-AP-MR01.1_512M32_DDR4_LM256.elf",
			"xblconfig-AP-MR01.1_512M32_DDR4_LM512.elf",
			"xblconfig-AP-MR01.1_2048M32_DDR4.elf"
		],
		"RDP464-C2/AP-MR01.1-C2": [
			"xblconfig-AP-MR01.1-C2_512M32_DDR4.elf",
			"xblconfig-AP-MR01.1-C2_512M32_DDR4_LM256.elf",
			"xblconfig-AP-MR01.1-C2_512M32_DDR4_LM512.elf",
			"xblconfig-AP-MR01.1-C2_2048M32_DDR4.elf"
		],
		"RDP464-C3/AP-MR01.1-C3": [
			"xblconfig-AP-MR01.1-C3_512M32_DDR4.elf",
			"xblconfig-AP-MR01.1-C3_512M32_DDR4_LM256.elf",
			"xblconfig-AP-MR01.1-C3_512M32_DDR4_LM512.elf",
			"xblconfig-AP-MR01.1-C3_2048M32_DDR4.elf"
		],
		"RDP466/AP-MR02.1": [
			"xblconfig-AP-MR02.1_256M32_DDR4.elf",
			"xblconfig-AP-MR02.1_256M32_DDR4_LM256.elf",
			"xblconfig-AP-MR02.1_256M32_DDR4_LM512.elf",
			"xblconfig-AP-MR02.1_512M32_DDR4.elf",
			"xblconfig-AP-MR02.1_2048M32_DDR4.elf"
		],
		"RDP466-C2/AP-MR02.1-C2": [
			"xblconfig-AP-MR02.1-C2_256M32_DDR4.elf",
			"xblconfig-AP-MR02.1-C2_256M32_DDR4_LM256.elf",
			"xblconfig-AP-MR02.1-C2_256M32_DDR4_LM512.elf",
			"xblconfig-AP-MR02.1-C2_512M32_DDR4.elf",
			"xblconfig-AP-MR02.1-C2_2048M32_DDR4.elf"
		],
		"RDP466-C3/AP-MR02.1-C3": [
			"xblconfig-AP-MR02.1-C3_256M32_DDR4.elf",
			"xblconfig-AP-MR02.1-C3_256M32_DDR4_LM256.elf",
			"xblconfig-AP-MR02.1-C3_256M32_DDR4_LM512.elf",
			"xblconfig-AP-MR02.1-C3_512M32_DDR4.elf",
			"xblconfig-AP-MR02.1-C3_2048M32_DDR4.elf"
		],
		"RDP466-RFFE/AP-MR02.1-RFFE": [
			"xblconfig-AP-MR02.1-RFFE_256M32_DDR4.elf",
			"xblconfig-AP-MR02.1-RFFE_256M32_DDR4_LM256.elf",
			"xblconfig-AP-MR02.1-RFFE_256M32_DDR4_LM512.elf",
			"xblconfig-AP-MR02.1-RFFE_512M32_DDR4.elf",
			"xblconfig-AP-MR02.1-RFFE_2048M32_DDR4.elf"
		],
		"RDP485/AP-MR02.2": [
			"xblconfig-AP-MR02.2_256M32_DDR4.elf",
			"xblconfig-AP-MR02.2_256M32_DDR4_LM256.elf",
			"xblconfig-AP-MR02.2_256M32_DDR4_LM512.elf",
			"xblconfig-AP-MR02.2_512M32_DDR4.elf",
			"xblconfig-AP-MR02.2_2048M32_DDR4.elf"
		],
		"RDP485-C2/AP-MR02.2-C2": [
			"xblconfig-AP-MR02.2-C2_256M32_DDR4.elf",
			"xblconfig-AP-MR02.2-C2_256M32_DDR4_LM256.elf",
			"xblconfig-AP-MR02.2-C2_256M32_DDR4_LM512.elf",
			"xblconfig-AP-MR02.2-C2_512M32_DDR4.elf",
			"xblconfig-AP-MR02.2-C2_2048M32_DDR4.elf"
		],
		"RDP485-C3/AP-MR02.2-C3": [
			"xblconfig-AP-MR02.2-C3_256M32_DDR4.elf",
			"xblconfig-AP-MR02.2-C3_256M32_DDR4_LM256.elf",
			"xblconfig-AP-MR02.2-C3_256M32_DDR4_LM512.elf",
			"xblconfig-AP-MR02.2-C3_512M32_DDR4.elf",
			"xblconfig-AP-MR02.2-C3_2048M32_DDR4.elf"
		],
		"RDP485-RFFE/AP-MR02.2-RFFE": [
			"xblconfig-AP-MR02.2-RFFE_256M32_DDR4.elf",
			"xblconfig-AP-MR02.2-RFFE_256M32_DDR4_LM256.elf",
			"xblconfig-AP-MR02.2-RFFE_256M32_DDR4_LM512.elf",
			"xblconfig-AP-MR02.2-RFFE_512M32_DDR4.elf",
			"xblconfig-AP-MR02.2-RFFE_2048M32_DDR4.elf"
		],
		"RDP485-RFFE-C2/AP-MR02.2-RFFE-C2": [
			"xblconfig-AP-MR02.2-RFFE-C2_256M32_DDR4.elf",
			"xblconfig-AP-MR02.2-RFFE-C2_256M32_DDR4_LM256.elf",
			"xblconfig-AP-MR02.2-RFFE-C2_256M32_DDR4_LM512.elf",
			"xblconfig-AP-MR02.2-RFFE-C2_512M32_DDR4.elf",
			"xblconfig-AP-MR02.2-RFFE-C2_2048M32_DDR4.elf"
		],
		"RDP496/AP-MR02.3": [
			"xblconfig-AP-MR02.3_256M32_DDR4.elf",
			"xblconfig-AP-MR02.3_256M32_DDR4_LM256.elf",
			"xblconfig-AP-MR02.3_256M32_DDR4_LM512.elf",
			"xblconfig-AP-MR02.3_512M32_DDR4.elf",
			"xblconfig-AP-MR02.3_2048M32_DDR4.elf"
		],
		"RDP487/AP-MR03.1": [
			"xblconfig-AP-MR03.1_256M16_DDR3.elf",
			"xblconfig-AP-MR03.1_256M16_DDR3_LM256.elf",
			"xblconfig-AP-MR03.1_256M16_DDR3_LM512.elf"
		],
		"DB-MR01.1": [
			"xblconfig-DB-MR01.1_512M32_DDR4.elf",
			"xblconfig-DB-MR01.1_512M32_DDR4_LM256.elf",
			"xblconfig-DB-MR01.1_512M32_DDR4_LM512.elf",
			"xblconfig-DB-MR01.1_2048M32_DDR4.elf"
		]
	}

	if board_type in board_file_map:
		for file_name in board_file_map[board_type]:
			if os.path.isfile(os.path.join(boot_build_path, file_name)):
				xblconfig_file = file_name
				break

	return xblconfig_file

def change_directory_and_execute(cmd, local_folder):
	os.chdir(local_folder)
	try:
		subprocess.call(cmd, shell=True)
		print("Executed command successfully")
	except subprocess.CalledProcessError as e:
		print("Error executing command: %s" % e)

def execute_initial_qsaharaserver_cmd(local_folder, port_num, xbl_file):
	qsahara_path = os.path.join(local_folder, "QSaharaServer.exe")
	if not os.path.isfile(qsahara_path):
		print("QSaharaServer.exe not found at %s" % qsahara_path)
		return

	initial_cmd = ".\\QSaharaServer.exe -p \\\\.\\COM%s -s 13:%s -v 3" % (port_num, xbl_file)
	change_directory_and_execute(initial_cmd, local_folder)

def construct_qsaharaserver_cmd(port_num, uboot_file, target_type, cdtbin_file, xblconfig_file=None):
	cmd = ".\\QSaharaServer.exe -p \\\\.\\COM%s -s 1:%s -s 34:devcfg.mbn -s 25:tz.mbn -s 5:%s" % (port_num, cdtbin_file, uboot_file)

	if target_type == "IPQ54xx":
		cmd += " -s 41:devcfg.mbn -s 25:tz.mbn"
		if xblconfig_file:
			cmd += " -s 38:%s" % xblconfig_file
	elif target_type == "IPQ95xx":
		cmd += " -s 23:rpm.mbn -s 35:apdp.mbn -s 37:tmel-ipq95xx-firmware.elf"
	elif target_type == "IPQ53xx":
		cmd += " -s 37:tmel-ipq53xx-patch.elf"

	cmd += " -v 3"
	return cmd

def copy_files_to_local_folder(files, boot_build_path, local_folder):
	if not os.path.exists(local_folder):
		os.makedirs(local_folder)

	for file in files:
		if file:
			src = os.path.join(boot_build_path, file)
			dst = os.path.join(local_folder, file)
			if os.path.isfile(src):
				shutil.copy(src, dst)
				print("Copied %s to %s" % (file, local_folder))


def main():
	parser = argparse.ArgumentParser(
		description="EDL Recovery Script for Qualcomm IPQ targets",
		formatter_class=argparse.RawTextHelpFormatter,
		epilog="""\
Example usage:
  python EDL_recovery.py -b /path/to/ipq -t IPQ95xx -d RDP417/AP.AL01-C1 -f EMMC -p 3

Arguments:
  -b, --boot_path   Path to the IPQ boot build folder
  -t, --target      Target type (e.g., IPQ95xx, IPQ53xx, IPQ54xx)
  -d, --board       Board type (e.g., RDP417/AP.AL01-C1)
  -f, --flash       Flash type (e.g., NAND, NORPLUSNAND, EMMC, NORPLUSEMMC)
  -p, --port        COM port number (e.g., 3)

If any argument is missing, the script will prompt you interactively.
"""
)

	parser.add_argument("-b", "--boot_path", help="Boot build path")
	parser.add_argument("-t", "--target", help="Target type")
	parser.add_argument("-d", "--board", help="Board type")
	parser.add_argument("-f", "--flash", help="Flash type")
	parser.add_argument("-p", "--port", help="COM port number")
	args = parser.parse_args()

	boot_build_path = args.boot_path or input("Enter the IPQ Folder Path: ")

	qsahara_path = os.path.join(boot_build_path, "QSaharaServer.exe")
	if not os.path.isfile(qsahara_path):
		print("Error: QSaharaServer.exe not found in the specified boot path.")
		exit(1)

	target_type = args.target or prompt_target_type()

	board_type_input = args.board
	if board_type_input:
		# Define board_types based on target_type
		if target_type == "IPQ95xx":
			board_types = ["RDP417/AP.AL01-C1", "RDP418/AP.AL02-C1", "RDP418-EMMC/AP.AL02-C2", "RDP437/AP.AL02-C3", "RDP433/AP.AL02-C4", "AP.AL02-C5", "RDP449/AP.AL02-C6", "RDP433-EMMC/AP.AL02-C7", "RDP453/AP.AL02-C8", "RDP454/AP.AL02-C9", "AP.AL02-C10", "RDP455-C11/AP.AL02-C11", "RDP455-C12/AP.AL02-C12", "RDP459/AP.AL02-C13", "AP.AL02-C14", "RDP457/AP.AL02-C15", "RDP456/AP.AL02-C16", "RDP469/AP.AL02-C17", "AP.AL02-C18", "RDP461/AP.AL02-C19", "RDP467/AP.AL02-C20", "AP.AL03-C1", "RDP458/AP.AL03-C2", "RDP475/AP.AL05", "RDP475-QCA81XX/AP.AL05-QCA81XX", "RDP475-QCA81XX-I2C/AP.AL05-QCA81XX-I2C", "RDP476/AP.AL06", "DB.AL01-C1", "DB.AL01-C2", "DB.AL01-C3", "DB.AL02-C1", "DB.AL02-C2", "DB.AL02-C3"]
		elif target_type == "IPQ53xx":
			board_types = ["RDP441/AP-MI01.2", "RDP441-QCA81XX/AP-MI01.2-QCA81XX", "RDP441-QCA81XX-I2C/AP-MI01.2-QCA81XX-I2C", "RDP484/AP-MI01.2-C2", "RDP472/AP-MI01.2-QCN9160-C1", "RDP442​/AP-MI01.3", "RDP477​/AP-MI01.3-C2", "RDP486​/AP-MI01.3-C3", "RDP477-256M/AP-MI01.3-C4", "RDP444/AP-MI01.4", "RDP468/AP-MI01.6 ", "RDP473/AP-MI01.7", "RDP474/AP-MI01.9", "RDP479/AP-MI01.12", "RDP480/AP-MI01.13", "RDP481/AP-MI01.14", "RDP447/AP-MI03.1", "RDP446/AP-MI04.1", "RDP478/AP-MI04.1-C2", "RDP478-256M/AP-MI04.1-C3", "RDP483/AP-MI04.3", "TB-MI03.1", "TB-MI05.1", "DB-MI01.1", "DB-MI02.1", "DB-MI03.1"]
		elif target_type == "IPQ54xx":
			board_types = ["RDP464/AP-MR01.1", "RDP464-C2/AP-MR01.1-C2", "RDP464-C3/AP-MR01.1-C3", "RDP466/AP-MR02.1", "RDP466-C2/AP-MR02.1-C2", "RDP466-C3/AP-MR02.1-C3", "RDP466-RFFE/AP-MR02.1-RFFE", "RDP485/AP-MR02.2", "RDP485-C2/AP-MR02.2-C2", "RDP485-C3/AP-MR02.2-C3", "RDP485-RFFE/AP-MR02.2-RFFE", "RDP485-RFFE-C2/AP-MR02.2-RFFE-C2", "RDP496/AP-MR02.3", "RDP487/AP-MR03.1", "DB-MR01.1"]

		matching_boards = [b for b in board_types if b.startswith(board_type_input + "/") or b.endswith("/" + board_type_input) or b == board_type_input]

		if len(matching_boards) == 1:
			board_type = matching_boards[0]
		else:
			print(f"Error: Invalid board type input '{board_type_input}'. Must match exactly one known board type.")
			exit(1)

	else:
		board_type = prompt_board_type(target_type)

	flash_type = args.flash or prompt_flash_type()
	port_num = args.port or input("Enter the port number: ")

	print("\nYou have selected the following options:")
	print("BootBuildPath: %s" % boot_build_path)
	print("TargetType: %s" % target_type)
	if board_type:
		print("BoardType: %s" % board_type)
	print("FlashType: %s" % flash_type)
	print("port_num: %s" % port_num)

	uboot_file = get_uboot_file(boot_build_path, flash_type, target_type)
	xbl_file = get_xbl_file(boot_build_path, target_type)
	cdtbin_file = get_cdtbin_file(boot_build_path, board_type, target_type)
	xblconfig_file = get_xblconfig_file(boot_build_path, board_type) if target_type == "IPQ54xx" else None

	local_folder = os.path.join(os.getcwd(), target_type)
	if target_type == "IPQ95xx":
		files_to_copy = [xbl_file, cdtbin_file, "devcfg.mbn", "tz.mbn", uboot_file, "tmel-ipq95xx-firmware.elf", "rpm.mbn", "apdp.mbn", "QSaharaServer.exe"]
	elif target_type == "IPQ53xx":
		files_to_copy = [xbl_file, cdtbin_file, "devcfg.mbn", "tz.mbn", uboot_file, "tmel-ipq53xx-patch.elf", "QSaharaServer.exe"]
	elif target_type == "IPQ54xx":
		files_to_copy = [xbl_file, xblconfig_file, "devcfg.mbn", "tz.mbn", uboot_file, "QSaharaServer.exe"]

	# Remove None values from files_to_copy list
	files_to_copy = [file for file in files_to_copy if file]

	copy_files_to_local_folder(files_to_copy, boot_build_path, local_folder)

	execute_initial_qsaharaserver_cmd(local_folder, port_num, xbl_file)
	time.sleep(5)
	cmd = construct_qsaharaserver_cmd(port_num, uboot_file, target_type, cdtbin_file, xblconfig_file)
	change_directory_and_execute(cmd, local_folder)

if __name__ == "__main__":
	main()
