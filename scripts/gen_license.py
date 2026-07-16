#!/usr/bin/python
# ===========================================================================
# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: ISC
# ===========================================================================

import xml.etree.ElementTree as ET
import os
import subprocess
import sys
from getopt import getopt
from getopt import GetoptError

def gen_license(arch, fltype, size, out_name):
    global cdir

    if (arch == "ipq5424"):
        prc = subprocess.Popen(['python', lic_script_path, '--flash', fltype,
            '--size', size, '--soc', soc_dir, '--output_dir', cdir, '--output_file', out_name])
    else:
        prc = subprocess.Popen(['python', lic_script_path, '--flash', fltype,
            '--size', size, '--soc', soc_dir, '--attach1', attach1_dir, '--attach2',
            attach2_dir, '--attach3', attach3_dir, '--attach4', attach4_dir,
            '--attach5', attach5_dir, '--output_dir', cdir, '--output_file', out_name])
    prc.wait()
    if prc.returncode != 0:
        print('ERROR: Generating license bin for ' + fltype + ' flash type')
        return -1

    return 0

def find_license_partition(file):
    global cdir
    global xml_path
    global flash_type
    global size

    part_found = 0
    flash_xml_path = xml_path + '/' + file
    xml = ET.parse(flash_xml_path)
    root = xml.getroot()
    parts = root.find(".//partitions")

    for node in parts:
        name = node.find('name').text
        size = node.find('size_kb').text
        if name == "0:LICENSE":
            part_found = 1
            break

    return (part_found, node, size)

def process_nor_license(arch, flash, xml_files):
    global cdir
    global xml_path
    global flash_type
    global size

    part_found = 0

    for file in xml_files:
        (part_found, node, size) = find_license_partition(file)
        if not part_found:
            print("LICENSE partition not found for",file)
            return -1
        out_name = file.split('.')[0]
        if gen_license(arch, 'nor', size, "license_" + out_name) < 0:
            return -1

    return 0

def process_nand_license(arch, flash, xml_files):
    global cdir
    global xml_path
    global flash_type
    global size

    part_found = 0

    for file in xml_files:
        (part_found, node, size) = find_license_partition(file)
        if not part_found:
            print("LICENSE partition not found for",file)
            return -1
        if '4k' not in file:
            out_name = file.split('.')[0]
            if gen_license(arch, 'nand2k', size, "license_" + out_name) < 0:
                return -1
        else:
            out_name = file.split('.')[0]
            if gen_license(arch, 'nand4k', size, "license_" + out_name) < 0:
                return -1

    return 0

def process_norplusnand_license(arch, flash, xml_files):
    global cdir
    global xml_path
    global flash_type
    global size

    part_found = 0

    for file in xml_files:
        (part_found, node, size) = find_license_partition(file)
        if not part_found:
            print("LICENSE partition not found for",file)
            return -1
        out_name = file.split('.')[0]
        which_flash = node.find('which_flash').text
        if which_flash == '1':
            if '4k' not in file:
                if gen_license(arch, 'nand2k', size, "license_" + out_name) < 0:
                    return -1
            else:
                if gen_license(arch, 'nand4k', size, "license_" + out_name) < 0:
                    return -1
        else:
            if gen_license(arch, 'nor', size, "license_" + out_name) < 0:
                return -1

    return 0

def process_norplusemmc_license(arch, flash, xml_files):
    global cdir
    global xml_path
    global flash_type
    global size

    part_found = 0

    try:
        file = xml_files[0]
        (part_found, node, size) = find_license_partition(file)
        if not part_found:
            raise Exception("License partition not found for",file)
        out_name = file.split('.')[0]
        if gen_license(arch, 'nor', size, "license_" + out_name) < 0:
            return -1
    except:
        file = xml_files[1]
        flash_xml_path = xml_path + '/' + file
        xml = ET.parse(flash_xml_path)
        root = xml.getroot()
        part = root.find(".//physical_partition[@ref='norplusemmc']/partition[@label='0:LICENSE']")
        if part is None:
            print('0:LICENSE partition not found for',file)
            return -1
        size = part.attrib['size_in_kb']
        out_name = file.split('.')[0]
        if gen_license(arch, 'emmc', size, "license_" + out_name) < 0:
            return -1

    return 0

def process_emmc_license(arch, flash, xml_files):
    global cdir
    global xml_path
    global flash_type
    global size

    for file in xml_files:
        flash_xml_path = xml_path + '/' + file
        xml = ET.parse(flash_xml_path)
        root = xml.getroot()
        part = root.find(".//physical_partition/partition[@label='0:LICENSE']")
        if part is None:
            print('0:LICENSE partition not found for',file)
            return -1
        size = part.attrib['size_in_kb']
        out_name = file.split('.')[0]
        if gen_license(arch, 'emmc', size, "license_" + out_name) < 0:
            return -1

    return 0

def process_norplusnand_gpt_license(arch, flash, xml_files):
    global cdir
    global xml_path
    global flash_type
    global size

    for file in xml_files:
        flash_xml_path = xml_path + '/' + file
        xml = ET.parse(flash_xml_path)
        root = xml.getroot()

        # Process for 2k layout
        layout = root.find(".//physical_partition[@ref='norplusnand-gpt']")
        if layout is None:
            print('norplusnand-gpt layout not found')
            return -1
        out_name = layout.attrib['ref']
        part = layout.find(".//partition[@label='0:LICENSE']")
        if part is None:
            print('0:LICENSE partition not found for',file)
            return -1
        size = part.attrib['size_in_kb']
        which_flash = part.attrib['flash_type']
        if which_flash == 'nand':
            if gen_license(arch, 'nand2k', size, "license_" + out_name) < 0:
                return -1
        else:
            if gen_license(arch, 'nor', size, "license_" + out_name) < 0:
                return -1

        # Process for 4k layout
        layout = root.find(".//physical_partition[@ref='norplusnand-4k-gpt']")
        if layout is None:
            print('norplusnand-4k-gpt layout not found')
            return -1
        out_name = layout.attrib['ref']
        part = layout.find(".//partition[@label='0:LICENSE']")
        if part is None:
            print('0:LICENSE partition not found for',file)
            return -1
        size = part.attrib['size_in_kb']
        which_flash = part.attrib['flash_type']
        if which_flash == 'nand':
            if gen_license(arch, 'nand4k', size, "license_" + out_name) < 0:
                return -1
        else:
            if gen_license(arch, 'nor', size, "license_" + out_name) < 0:
                return -1

    return 0

def process_norplusemmc_gpt_license(arch, flash, xml_files):
    global cdir
    global xml_path
    global flash_type
    global size

    try:
        file = xml_files[0]
        flash_xml_path = xml_path + '/' + file
        xml = ET.parse(flash_xml_path)
        root = xml.getroot()
        layout = root.find(".//physical_partition[@ref='norplusemmc-gpt']")
        if layout is None:
            print('norplusemmc-gpt layout not found')
            return -1
        out_name = layout.attrib['ref']
        part = layout.find(".//partition[@label='0:LICENSE']")
        if part is None:
            raise Exception('0:LICENSE partition not found in nor flash for',file)
        size = part.attrib['size_in_kb']
        if gen_license(arch, 'nor', size, "license_" + out_name) < 0:
            return -1
    except:
        file = xml_files[1]
        flash_xml_path = xml_path + '/' + file
        xml = ET.parse(flash_xml_path)
        root = xml.getroot()
        part = root.find(".//physical_partition[@ref='norplusemmc']/partition[@label='0:LICENSE']")
        if part is None:
            print('0:LICENSE partition not found for',file)
            return -1
        size = part.attrib['size_in_kb']
        if gen_license(arch, 'emmc', size, "license_" + out_name) < 0:
            return -1

    return 0

def main():
    global cdir
    global soc_dir
    global attach1_dir
    global attach2_dir
    global attach3_dir
    global attach4_dir
    global attach5_dir
    global xml_path
    global lic_script_path
    global flash_type
    global size

    funcdict_license = {
            'tiny-nor': [process_nor_license, ["nor-partition.xml"]],
            'tiny-nor-debug': [process_nor_license, ["nor-partition.xml"]],
            'nor': [process_nor_license, ["nor-partition.xml"]],
            'nand': [process_nand_license, ["nand-partition.xml", "nand-4k-partition.xml"]],
            'norplusnand': [process_norplusnand_license, ["norplusnand-partition.xml", "norplusnand-4k-partition.xml"]],
            'norplusnand-gpt': [process_norplusnand_gpt_license, ["nor-gpt-partition.xml"]],
            'norplusemmc': [process_norplusemmc_license, ['norplusemmc-partition.xml', 'sec-emmc-partition.xml']],
            'norplusemmc-gpt': [process_norplusemmc_gpt_license, ["nor-gpt-partition.xml", "sec-emmc-partition.xml"]],
            'emmc': [process_emmc_license, ["emmc-partition.xml", "emmc-partition-vendor.xml"]],
    }

    if len(sys.argv) > 1:
        try:
            opts, args = getopt(sys.argv[1:], "h", ["arch=", "fltype=", "in=", "soc=", "attach1=", "attach2=", "attach3=", "attach4=", "attach5"]);
        except GetoptError as e:
            print('Arch, Flash type and Licenses are required to generate license blob')
            raise

        for option, value in opts:
            if option == "--arch":
                arch = value
            elif option == "--fltype":
                flash = value
            elif option == "--in":
                cdir = value
            elif option == "--soc":
                soc_dir = value

        if arch != "ipq5424":
            for option, value in opts:
                if option == "--attach1":
                    attach1_dir = value
                elif option == "--attach2":
                    attach2_dir = value
                elif option == "--attach3":
                    attach3_dir = value
                elif option == "--attach4":
                    attach4_dir = value
                elif option == "--attach5":
                    attach5_dir = value

        xml_path = "$$/" + arch + "/flash_partition"
        xml_path = xml_path.replace('$$', cdir)
        lic_script_path = cdir + '/scripts/gen_license_blob.py'

        if funcdict_license[flash][0](arch, flash, funcdict_license[flash][1]) < 0:
            return -1
    else:
        print('Arch, Flash type and Licenses are required to generate license blob')
        return -1

    return 0

if __name__ == '__main__':
    main()
