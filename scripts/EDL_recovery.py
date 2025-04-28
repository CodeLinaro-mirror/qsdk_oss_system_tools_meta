# ===========================================================================
# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: ISC
# ===========================================================================

try: input = raw_input
except NameError: raw_input = input

import os
import subprocess
import time
import shutil

def get_user_input():
	boot_build_path = raw_input("Enter the IPQ Folder Path: ")

	target_types = ["IPQ9574", "IPQ5332", "IPQ5424"]
	print("Choose the TargetType from the following options:")
	for i, target in enumerate(target_types, 1):
		print("%d. %s" % (i, target))

	target_type_index = int(raw_input("Enter the number corresponding to your choice: ")) - 1
	target_type = target_types[target_type_index]

	board_type = None
	if target_type == "IPQ9574":
		board_types = ["AL-EMU", "AP.AL01-C1", "AP.AL02-C1", "AP.AL02-C2", "AP.AL02-C3", "AP.AL02-C4", "AP.AL02-C5", "AP.AL02-C6", "AP.AL02-C7", "AP.AL02-C8", "AP.AL02-C9", "AP.AL02-C10", "AP.AL02-C11", "AP.AL02-C12", "AP.AL02-C13", "AP.AL02-C14", "AP.AL02-C15", "AP.AL02-C16", "AP.AL02-C17", "AP.AL02-C18", "AP.AL02-C19", "AP.AL02-C20", "AP.AL03-C1", "AP.AL03-C2", "AP.AL05", "AP.AL05-QCA81XX", "AP.AL05-QCA81XX-I2C", "AP.AL06", "DB.AL01-C1", "DB.AL01-C2", "DB.AL01-C3", "DB.AL02-C1", "DB.AL02-C2", "DB.AL02-C3"]
	elif target_type == "IPQ5332":
		board_types = ["MI-EMU", "AP-MI01.2", "AP-MI01.2-QCA81XX", "AP-MI01.2-QCA81XX-I2C", "AP-MI01.2-C2", "AP-MI01.2-QCN9160-C1", "AP-MI01.3", "AP-MI01.3-C2", "AP-MI01.3-C3", "AP-MI01.3-C4", "AP-MI01.4", "AP-MI01.6", "AP-MI01.7", "AP-MI01.9", "AP-MI01.12", "AP-MI01.13", "AP-MI01.14", "AP-MI03.1", "AP-MI04.1", "AP-MI04.1-C2", "AP-MI04.1-C3", "AP-MI04.3", "TB-MI03.1", "TB-MI05.1", "DB-MI01.1", "DB-MI02.1", "DB-MI03.1"]
	elif target_type == "IPQ5424":
		board_types = ["MA-EMU", "AP-MR01.1", "AP-MR01.1-C2", "AP-MR01.1-C3", "AP-MR02.1", "AP-MR02.1-C2", "AP-MR02.1-C3", "AP-MR02.1-RFFE", "AP-MR02.2", "AP-MR02.2-C2", "AP-MR02.2-C3", "AP-MR02.2-RFFE", "AP-MR02.2-RFFE-C2", "AP-MR02.3", "AP-MR03.1", "DB-MR01.1"]

	port_num = raw_input("Enter the port number: ")

	if board_types:
		print("Choose the BoardType from the following options:")
		for i, board in enumerate(board_types, 1):
			print("%d. %s" % (i, board))

		board_type_index = int(raw_input("Enter the number corresponding to your choice: ")) - 1
		board_type = board_types[board_type_index]

	flash_types = ["NAND", "NORPlusNAND", "eMMC", "NORPlusEMMC"]
	print("Choose the FlashType from the following options:")
	for i, flash in enumerate(flash_types, 1):
		print("%d. %s" % (i, flash))

	flash_type_index = int(raw_input("Enter the number corresponding to your choice: ")) - 1
	flash_type = flash_types[flash_type_index]

	return boot_build_path, target_type, board_type, flash_type, port_num

def get_cdtbin_file(boot_build_path, board_type, target_type):
	cdtbin_file = None
	board_file_map = {
		"AP.AL01-C1": ["cdt-AP-AL01-C1_256M32_DDR3.bin", "cdt-AP-AL01-C1_256M32_DDR3_LM512.bin"],
		"AP.AL02-C1": ["cdt-AP-AL02-C1_256M32_DDR4.bin", "cdt-AP-AL02-C1_256M32_DDR4_LM512.bin"],
		"AP.AL02-C2": ["cdt-AP-AL02-C2_256M32_DDR4.bin", "cdt-AP-AL02-C2_256M32_DDR4_LM512.bin"],
		"AP.AL02-C3": ["cdt-AP-AL02-C3_256M32_DDR4.bin", "cdt-AP-AL02-C3_256M32_DDR4_LM512.bin"],
		"AP.AL02-C4": ["cdt-AP-AL02-C4_256M32_DDR4.bin", "cdt-AP-AL02-C4_256M32_DDR4_LM512.bin"],
		"AP.AL02-C5": ["cdt-AP-AL02-C5_256M32_DDR4.bin", "cdt-AP-AL02-C5_256M32_DDR4_LM512.bin"],
		"AP.AL02-C6": ["cdt-AP-AL02-C6_256M32_DDR4.bin", "cdt-AP-AL02-C6_256M32_DDR4_LM512.bin"],
		"AP.AL02-C7": ["cdt-AP-AL02-C7_256M32_DDR4.bin", "cdt-AP-AL02-C7_256M32_DDR4_LM512.bin"],
		"AP.AL02-C8": ["cdt-AP-AL02-C8_256M32_DDR4.bin", "cdt-AP-AL02-C8_256M32_DDR4_LM512.bin"],
		"AP.AL02-C9": ["cdt-AP-AL02-C9_256M32_DDR4.bin", "cdt-AP-AL02-C9_256M32_DDR4_LM512.bin"],
		"AP.AL02-C10": ["cdt-AP-AL02-C10_256M32_DDR4.bin", "cdt-AP-AL02-C10_256M32_DDR4_LM512.bin"],
		"AP.AL02-C11": ["cdt-AP-AL02-C11_512M32_DDR4.bin", "cdt-AP-AL02-C11_512M32_DDR4_LM512.bin"],
		"AP.AL02-C12": ["cdt-AP-AL02-C12_256M32_DDR4.bin", "cdt-AP-AL02-C12_256M32_DDR4_LM512.bin"],
		"AP.AL02-C13": ["cdt-AP-AL02-C13_256M32_DDR4.bin", "cdt-AP-AL02-C13_256M32_DDR4_LM512.bin"],
		"AP.AL02-C14": ["cdt-AP-AL02-C14_256M16_DDR4.bin", "cdt-AP-AL02-C14_256M16_DDR4_LM512.bin"],
		"AP.AL02-C15": ["cdt-AP-AL02-C15_256M32_DDR4.bin", "cdt-AP-AL02-C15_256M32_DDR4_LM512.bin"],
		"AP.AL02-C16": ["cdt-AP-AL02-C16_512M32_DDR4.bin", "cdt-AP-AL02-C16_512M32_DDR4_LM512.bin"],
		"AP.AL02-C17": ["cdt-AP-AL02-C17_256M32_DDR4.bin", "cdt-AP-AL02-C17_256M32_DDR4_LM512.bin"],
		"AP.AL02-C18": ["cdt-AP-AL02-C18_256M32_DDR4.bin", "cdt-AP-AL02-C18_256M32_DDR4_LM512.bin"],
		"AP.AL02-C19": ["cdt-AP-AL02-C19_256M32_DDR4.bin", "cdt-AP-AL02-C19_256M32_DDR4_LM512.bin"],
		"AP.AL02-C20": ["cdt-AP-AL02-C20_512M32_DDR4.bin", "cdt-AP-AL02-C20_512M32_DDR4_LM512.bin"],
		"AP.AL03-C1": ["cdt-AP-AL03-C1_256M32_DDR3.bin", "cdt-AP-AL03-C1_256M32_DDR3_LM512.bin"],
		"AP.AL03-C2": ["cdt-AP-AL03-C2_256M32_DDR3.bin", "cdt-AP-AL03-C2_256M32_DDR3_LM512.bin"],
		"AP.AL05": ["cdt-AP-AL05_256M32_DDR4.bin", "cdt-AP-AL05_256M32_DDR4_LM512.bin"],
		"AP.AL05-QCA81XX": ["cdt-AP-AL05-QCA81XX_256M32_DDR4.bin", "cdt-AP-AL05-QCA81XX_256M32_DDR4_LM512.bin"],
		"AP.AL05-QCA81XX-I2C": ["cdt-AP-AL05-QCA81XX-I2C_256M32_DDR4.bin", "cdt-AP-AL05-QCA81XX_256M32-I2C_DDR4_LM512.bin"],
		"AP.AL06": ["cdt-AP-AL06_256M32_DDR4.bin", "cdt-AP-AL06_256M32_DDR4_LM512.bin"],
		"DB.AL01-C1": ["cdt-DB-AL01-C1_256M32_DDR3.bin", "cdt-DB-AL01-C1_256M32_DDR3_LM512.bin"],
		"DB.AL01-C2": ["cdt-DB-AL01-C2_256M32_DDR3.bin", "cdt-DB-AL01-C2_256M32_DDR3_LM512.bin"],
		"DB.AL01-C3": ["cdt-DB-AL01-C3_256M32_DDR3.bin", "cdt-DB-AL01-C3_256M32_DDR3_LM512.bin"],
		"DB.AL02-C1": ["cdt-DB-AL02-C1_1024M32_DDR4.bin", "cdt-DB-AL02-C1_1024M32_DDR4_LM512.bin"],
		"DB.AL02-C2": ["cdt-DB-AL02-C2_1024M32_DDR4.bin", "cdt-DB-AL02-C2_1024M32_DDR4_LM512.bin"],
		"DB.AL02-C3": ["cdt-DB-AL02-C3_1024M32_DDR4.bin", "cdt-DB-AL02-C3_1024M32_DDR4_LM512.bin"],
		"MI-EMU": ["cdt-MI-EMU_512M16_DDR4.bin", "cdt-MI-EMU_512M16_DDR4_LM512.bin", "cdt-MI-EMU_512M16_DDR4_LM256.bin"],
		"AP-MI01.2": ["cdt-AP-MI01.2_512M16_DDR4.bin", "cdt-AP-MI01.2_512M16_DDR4_LM512.bin", "cdt-AP-MI01.2_512M16_DDR4_LM256.bin"],
		"AP-MI01.2-QCA81XX": ["cdt-AP-MI01.2-QCA81XX_512M16_DDR4.bin", "cdt-AP-MI01.2-QCA81XX_512M16_DDR4_LM512.bin", "cdt-AP-MI01.2-QCA81XX_512M16_DDR4_LM256.bin"],
		"AP-MI01.2-QCA81XX-I2C": ["cdt-AP-MI01.2-QCA81XX-I2C_512M16_DDR4.bin", "cdt-AP-MI01.2-QCA81XX-I2C_512M16_DDR4_LM512.bin"],
		"AP-MI01.2-C2": ["cdt-AP-MI01.2-C2_512M16_DDR4.bin", "cdt-AP-MI01.2-C2_512M16_DDR4_LM512.bin", "cdt-AP-MI01.2-C2_512M16_DDR4_LM256.bin"],
		"AP-MI01.2-QCN9160-C1": ["cdt-AP-MI01.2-QCN9160-C1_512M16_DDR4.bin", "cdt-AP-MI01.2-QCN9160-C1_512M16_DDR4_LM512.bin", "cdt-AP-MI01.2-QCN9160-C1_512M16_DDR4_LM256.bin"],
		"AP-MI01.3": ["cdt-AP-MI01.3_512M16_DDR4.bin", "cdt-AP-MI01.3_512M16_DDR4_LM512.bin", "cdt-AP-MI01.3_512M16_DDR4_LM256.bin"],
		"AP-MI01.3-C2": ["cdt-AP-MI01.3-C2_256M16_DDR4.bin", "cdt-AP-MI01.3-C2_256M16_DDR4_LM512.bin", "cdt-AP-MI01.3-C2_256M16_DDR4_LM256.bin"],
		"AP-MI01.3-C3": ["cdt-AP-MI01.3-C3_512M16_DDR4.bin", "cdt-AP-MI01.3-C3_512M16_DDR4_LM512.bin", "cdt-AP-MI01.3-C3_512M16_DDR4_LM256.bin"],
		"AP-MI01.3-C4": ["cdt-AP-MI01.3-C4_256M16_DDR4.bin", "cdt-AP-MI01.3-C4_256M16_DDR4_LM512.bin", "cdt-AP-MI01.3-C4_256M16_DDR4_LM256.bin"],
		"AP-MI01.12": ["cdt-AP-RDP479_512M16_DDR4.bin", "cdt-AP-RDP479_512M16_DDR4_LM512.bin", "cdt-AP-RDP479_512M16_DDR4_LM256.bin"],
		"AP-MI01.13": ["cdt-AP-MI01.13_512M16_DDR4.bin", "cdt-AP-MI01.13_512M16_DDR4_LM512.bin", "cdt-AP-MI01.13_512M16_DDR4_LM256.bin"],
		"AP-MI01.14": ["cdt-AP-RDP481_512M16_DDR4.bin", "cdt-AP-RDP481_512M16_DDR4_LM512.bin", "cdt-AP-RDP481_512M16_DDR4_LM256.bin"],
		"AP-MI01.4": ["cdt-AP-MI01.4_256M16_DDR4.bin", "cdt-AP-MI01.4_256M16_DDR4_LM512.bin", "cdt-AP-MI01.4_256M16_DDR4_LM256.bin"],
		"AP-MI01.6": ["cdt-AP-MI01.6_512M16_DDR4.bin", "cdt-AP-MI01.6_512M16_DDR4_LM512.bin", "cdt-AP-MI01.6_512M16_DDR4_LM256.bin"],
		"AP-MI01.7": ["cdt-AP-MI01.7_512M16_DDR4.bin", "cdt-AP-MI01.7_512M16_DDR4_LM512.bin", "cdt-AP-MI01.7_512M16_DDR4_LM256.bin"],
		"AP-MI01.9": ["cdt-AP-MI01.9_512M16_DDR4.bin", "cdt-AP-MI01.9_512M16_DDR4_LM512.bin", "cdt-AP-MI01.9_512M16_DDR4_LM256.bin"],
		"AP-MI03.1": ["cdt-AP-MI03.1_128M16_DDR3.bin", "cdt-AP-MI03.1_128M16_DDR3_LM512.bin", "cdt-AP-MI03.1_128M16_DDR3_LM256.bin"],
		"AP-MI04.1": ["cdt-AP-MI04.1_256M16_NOM_DDR4.bin", "cdt-AP-MI04.1_256M16_NOM_DDR4_LM512.bin", "cdt-AP-MI04.1_256M16_NOM_DDR4_LM256.bin"],
		"AP-MI04.1-C2": ["cdt-AP-MI04.1-C2_256M16_NOM_DDR4.bin", "cdt-AP-MI04.1-C2_256M16_NOM_DDR4_LM512.bin", "cdt-AP-MI04.1-C2_256M16_NOM_DDR4_LM256.bin"],
		"AP-MI04.1-C3": ["cdt-AP-MI04.1-C3_256M16_NOM_DDR4.bin", "cdt-AP-MI04.1-C3_256M16_NOM_DDR4_LM512.bin", "cdt-AP-MI04.1-C3_256M16_NOM_DDR4_LM256.bin"],
		"AP-MI04.3": ["cdt-AP-MI04.3_256M16_NOM_DDR4.bin", "cdt-AP-MI04.3_256M16_NOM_DDR4_LM512.bin", "cdt-AP-MI04.3_256M16_NOM_DDR4_LM256.bin"],
		"TB-MI03.1": ["cdt-TB-MI03.1_256M16_TB_DDR4.bin", "cdt-TB-MI03.1_256M16_TB_DDR4_LM512.bin", "cdt-TB-MI03.1_256M16_TB_DDR4_LM256.bin"],
		"TB-MI05.1": ["cdt-TB-MI05.1_256M16_TB_DDR3.bin", "cdt-TB-MI05.1_256M16_TB_DDR3_LM512.bin", "cdt-TB-MI05.1_256M16_TB_DDR3_LM256.bin"],
		"DB-MI01.1": ["cdt-DB-MI01.1_512M16_DDR4.bin", "cdt-DB-MI01.1_512M16_DDR4_LM512.bin", "cdt-DB-MI01.1_512M16_DDR4_LM256.bin"],
		"DB-MI02.1": ["cdt-DB-MI02.1_128M16_DDR3.bin", "cdt-DB-MI02.1_128M16_DDR3_LM512.bin", "cdt-DB-MI02.1_128M16_DDR3_LM256.bin"],
		"DB-MI03.1": ["cdt-DB-MI03.1_128M16_DDR3.bin", "cdt-DB-MI03.1_128M16_DDR3_LM512.bin", "cdt-DB-MI03.1_128M16_DDR3_LM256.bin"]
	}

	if target_type == "IPQ5424":
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
		"IPQ9574": {
			"eMMC": [
				"openwrt-ipq9574-ipq95xx_32-mmc32-u-boot.mbn",
				"openwrt-ipq9574-generic-mmc-u-boot.mbn"
			],
			"NORPlusEMMC": [
				"openwrt-ipq9574-ipq95xx_32-norplusmmc32-u-boot.mbn",
				"openwrt-ipq9574-generic-norplusmmc-u-boot.mbn"
			],
			"NAND": [
				"openwrt-ipq9574-ipq95xx_32-nand32-u-boot.mbn",
				"openwrt-ipq9574-generic-nand-u-boot.mbn"
			],
			"NORPlusNAND": [
				"openwrt-ipq9574-ipq95xx_32-norplusnand32-u-boot.mbn",
				"openwrt-ipq9574-generic-norplusnand-u-boot.mbn"
			]
		},
		"IPQ5332": {
			"eMMC": [
				"openwrt-ipq5332-ipq53xx_32-mmc32-u-boot.mbn",
				"openwrt-ipq5332-generic-mmc-u-boot.mbn"
			],
			"NORPlusEMMC": [
				"openwrt-ipq5332-ipq53xx_32-norplusmmc32-u-boot.mbn",
				"openwrt-ipq5332-generic-norplusmmc-u-boot.mbn"
			],
			"NAND": [
				"openwrt-ipq5332-ipq53xx_32-nand32-u-boot.mbn",
				"openwrt-ipq5332-generic-nand-u-boot.mbn"
			],
			"NORPlusNAND": [
				"openwrt-ipq5332-ipq53xx_32-norplusnand32-u-boot.mbn",
				"openwrt-ipq5332-generic-norplusnand-u-boot.mbn"
			]
		},
		"IPQ5424": {
			"eMMC": [
				"openwrt-ipq5424-generic-mmc-u-boot.mbn",
				"openwrt-ipq5424-ipq54xx_32-mmc32-u-boot.mbn"
			],
			"NORPlusEMMC": [
				"openwrt-ipq5424-generic-norplusmmc-u-boot.mbn",
				"openwrt-ipq5424-ipq54xx_32-norplusmmc32-u-boot.mbn"
			],
			"NAND": [
				"openwrt-ipq5424-generic-nand-u-boot.mbn",
				"openwrt-ipq5424-ipq54xx_32-nand32-u-boot.mbn"
			],
			"NORPlusNAND": [
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
		"IPQ9574": "xbl.elf",
		"IPQ5332": "xbl_flashless.elf",
		"IPQ5424": "xbl_s_flashless.melf"
	}

	xbl_file = xbl_file_map.get(target_type)
	if xbl_file and os.path.isfile(os.path.join(boot_build_path, xbl_file)):
		return xbl_file
	return None

def get_xblconfig_file(boot_build_path, board_type):
	xblconfig_file = None
	board_file_map = {
		"MA-EMU": [
			"xblconfig-MA-EMU_256M32_DDR4.elf",
			"xblconfig-MA-EMU_256M32_DDR4_LM256.elf",
			"xblconfig-MA-EMU_256M32_DDR4_LM512.elf",
			"xblconfig-MA-EMU_512M32_DDR4.elf",
			"xblconfig-MA-EMU_2048M32_DDR4.elf"
		],
		"AP-MR01.1": [
			"xblconfig-AP-MR01.1_512M32_DDR4.elf",
			"xblconfig-AP-MR01.1_512M32_DDR4_LM256.elf",
			"xblconfig-AP-MR01.1_512M32_DDR4_LM512.elf",
			"xblconfig-AP-MR01.1_2048M32_DDR4.elf"
		],
		"AP-MR01.1-C2": [
			"xblconfig-AP-MR01.1-C2_512M32_DDR4.elf",
			"xblconfig-AP-MR01.1-C2_512M32_DDR4_LM256.elf",
			"xblconfig-AP-MR01.1-C2_512M32_DDR4_LM512.elf",
			"xblconfig-AP-MR01.1-C2_2048M32_DDR4.elf"
		],
		"AP-MR01.1-C3": [
			"xblconfig-AP-MR01.1-C3_512M32_DDR4.elf",
			"xblconfig-AP-MR01.1-C3_512M32_DDR4_LM256.elf",
			"xblconfig-AP-MR01.1-C3_512M32_DDR4_LM512.elf",
			"xblconfig-AP-MR01.1-C3_2048M32_DDR4.elf"
		],
		"AP-MR02.1": [
			"xblconfig-AP-MR02.1_256M32_DDR4.elf",
			"xblconfig-AP-MR02.1_256M32_DDR4_LM256.elf",
			"xblconfig-AP-MR02.1_256M32_DDR4_LM512.elf",
			"xblconfig-AP-MR02.1_512M32_DDR4.elf",
			"xblconfig-AP-MR02.1_2048M32_DDR4.elf"
		],
		"AP-MR02.1-C2": [
			"xblconfig-AP-MR02.1-C2_256M32_DDR4.elf",
			"xblconfig-AP-MR02.1-C2_256M32_DDR4_LM256.elf",
			"xblconfig-AP-MR02.1-C2_256M32_DDR4_LM512.elf",
			"xblconfig-AP-MR02.1-C2_512M32_DDR4.elf",
			"xblconfig-AP-MR02.1-C2_2048M32_DDR4.elf"
		],
		"AP-MR02.1-C3": [
			"xblconfig-AP-MR02.1-C3_256M32_DDR4.elf",
			"xblconfig-AP-MR02.1-C3_256M32_DDR4_LM256.elf",
			"xblconfig-AP-MR02.1-C3_256M32_DDR4_LM512.elf",
			"xblconfig-AP-MR02.1-C3_512M32_DDR4.elf",
			"xblconfig-AP-MR02.1-C3_2048M32_DDR4.elf"
		],
		"AP-MR02.1-RFFE": [
			"xblconfig-AP-MR02.1-RFFE_256M32_DDR4.elf",
			"xblconfig-AP-MR02.1-RFFE_256M32_DDR4_LM256.elf",
			"xblconfig-AP-MR02.1-RFFE_256M32_DDR4_LM512.elf",
			"xblconfig-AP-MR02.1-RFFE_512M32_DDR4.elf",
			"xblconfig-AP-MR02.1-RFFE_2048M32_DDR4.elf"
		],
		"AP-MR02.2": [
			"xblconfig-AP-MR02.2_256M32_DDR4.elf",
			"xblconfig-AP-MR02.2_256M32_DDR4_LM256.elf",
			"xblconfig-AP-MR02.2_256M32_DDR4_LM512.elf",
			"xblconfig-AP-MR02.2_512M32_DDR4.elf",
			"xblconfig-AP-MR02.2_2048M32_DDR4.elf"
		],
		"AP-MR02.2-C2": [
			"xblconfig-AP-MR02.2-C2_256M32_DDR4.elf",
			"xblconfig-AP-MR02.2-C2_256M32_DDR4_LM256.elf",
			"xblconfig-AP-MR02.2-C2_256M32_DDR4_LM512.elf",
			"xblconfig-AP-MR02.2-C2_512M32_DDR4.elf",
			"xblconfig-AP-MR02.2-C2_2048M32_DDR4.elf"
		],
		"AP-MR02.2-C3": [
			"xblconfig-AP-MR02.2-C3_256M32_DDR4.elf",
			"xblconfig-AP-MR02.2-C3_256M32_DDR4_LM256.elf",
			"xblconfig-AP-MR02.2-C3_256M32_DDR4_LM512.elf",
			"xblconfig-AP-MR02.2-C3_512M32_DDR4.elf",
			"xblconfig-AP-MR02.2-C3_2048M32_DDR4.elf"
		],
		"AP-MR02.2-RFFE": [
			"xblconfig-AP-MR02.2-RFFE_256M32_DDR4.elf",
			"xblconfig-AP-MR02.2-RFFE_256M32_DDR4_LM256.elf",
			"xblconfig-AP-MR02.2-RFFE_256M32_DDR4_LM512.elf",
			"xblconfig-AP-MR02.2-RFFE_512M32_DDR4.elf",
			"xblconfig-AP-MR02.2-RFFE_2048M32_DDR4.elf"
		],
		"AP-MR02.2-RFFE-C2": [
			"xblconfig-AP-MR02.2-RFFE-C2_256M32_DDR4.elf",
			"xblconfig-AP-MR02.2-RFFE-C2_256M32_DDR4_LM256.elf",
			"xblconfig-AP-MR02.2-RFFE-C2_256M32_DDR4_LM512.elf",
			"xblconfig-AP-MR02.2-RFFE-C2_512M32_DDR4.elf",
			"xblconfig-AP-MR02.2-RFFE-C2_2048M32_DDR4.elf"
		],
		"AP-MR02.3": [
			"xblconfig-AP-MR02.3_256M32_DDR4.elf",
			"xblconfig-AP-MR02.3_256M32_DDR4_LM256.elf",
			"xblconfig-AP-MR02.3_256M32_DDR4_LM512.elf",
			"xblconfig-AP-MR02.3_512M32_DDR4.elf",
			"xblconfig-AP-MR02.3_2048M32_DDR4.elf"
		],
		"AP-MR03.1": [
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

	if target_type == "IPQ5424":
		cmd += " -s 41:devcfg.mbn -s 25:tz.mbn"
		if xblconfig_file:
			cmd += " -s 38:%s" % xblconfig_file
	elif target_type == "IPQ9574":
		cmd += " -s 23:rpm.mbn -s 35:apdp.mbn -s 37:tmel-ipq95xx-firmware.elf"
	elif target_type == "IPQ5332":
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
	boot_build_path, target_type, board_type, flash_type, port_num = get_user_input()

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
	xblconfig_file = get_xblconfig_file(boot_build_path, board_type) if target_type == "IPQ5424" else None

	local_folder = os.path.join(os.getcwd(), target_type)
	if target_type == "IPQ9574":
		files_to_copy = [xbl_file, cdtbin_file, "devcfg.mbn", "tz.mbn", uboot_file, "tmel-ipq95xx-firmware.elf", "rpm.mbn", "apdp.mbn", "QSaharaServer.exe"]
	elif target_type == "IPQ5332":
		files_to_copy = [xbl_file, cdtbin_file, "devcfg.mbn", "tz.mbn", uboot_file, "tmel-ipq53xx-patch.elf", "QSaharaServer.exe"]
	elif target_type == "IPQ5424":
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
