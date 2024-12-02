#!/usr/bin/python
# ===========================================================================
# Copyright (c) 2024, Qualcomm Innovation Center, Inc. All rights reserved.
# SPDX-License-Identifier: ISC
# ===========================================================================

import xml.etree.ElementTree as ET
import os
import subprocess
import sys
from getopt import getopt
from getopt import GetoptError
import json
import shutil

ARCH_NAME = ''

cdir = os.path.dirname("")
cdir = os.path.abspath(cdir)

def main():

    global cdir
    global outputdir
    global ARCH_NAME
    global memory_profile
    global dtcDir

    memory_profile = "default"
    if len(sys.argv) > 1:
        try:
            opts, args = getopt(sys.argv[1:], "c:o:m:", "dtc_path=")
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
    else:
        print("config file and output path are needed to generate xblcfg files")
        return -1

    tree = ET.parse(file_path)
    root = tree.getroot()

    machid = None
    board = None
    arch = root.find(".//data[@type='ARCH']/SOC")
    ARCH_NAME = str(arch.text)

    srcDir = '$$/' + ARCH_NAME + '/xblconfig_json'
    srcDir = srcDir.replace('$$', cdir)
    if not os.path.exists(srcDir):
        os.makedirs(srcDir)

    xblconfigtool_path = '$$/scripts/XBLConfig/'
    xblconfigtool_path = xblconfigtool_path.replace('$$', cdir)
    xblconfigtool_gen = '$$/scripts/XBLConfig/GenXBLConfig.py'
    xblconfigtool_gen = xblconfigtool_gen.replace('$$', cdir)
    xblconfig_path = '$$/xbl_config.elf'
    xblconfig_path = xblconfig_path.replace('$$', cdir)
    xblconfig_json = '$$/create_xbl_config.json'
    xblconfig_json = xblconfig_json.replace('$$', srcDir)

    #disassemble the xbl config
    print('Disassembling xblconfig')
    cmd = ['python', xblconfigtool_gen, '-d', xblconfig_path, '-fELF', '-o', srcDir, '--tools_path', xblconfigtool_path]
    print(cmd)
    prc = subprocess.Popen(cmd, cwd=cdir)
    prc.wait()
    if prc.returncode != 0:
        print('ERROR: unable to disassemble xbl config')
        return prc.returncode

    # add support to generate the xbl cust dtb
    print("Generating xbl cust dtb")
    dtcBin = os.path.join(dtcDir, "dtc")
    cmd = [dtcBin, '-@', '-O', 'dtb', '-o', srcDir + "/" + "xbl-cust-marina-1.0.dtb", cdir + "/ipq5424/xbl_config/xbl-cust-marina-1.0.dts"]
    print(cmd)
    prc = subprocess.Popen(cmd, cwd=cdir)
    prc.wait()
    if prc.returncode != 0:
        print('ERROR: unable to generate dtb')
        return prc.returncode

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

            if memory_profile == '256' or memory_profile == '512':
                name_suffix =  board.text + "_" + memory.text + "_LM" + memory_profile
            else:
                name_suffix =  board.text + "_" + memory.text

            cdt_bin =  "cdt-" + name_suffix + ".bin"

            # edit the cdt name in json
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

            outfile_json = os.path.join(srcDir, "create_xbl_config-" + name_suffix + ".json")
            with open(outfile_json, "w") as outfile:
                json.dump(Data, outfile)

            #copy the cdt bin
            shutil.copy2(cdir+'/'+cdt_bin, srcDir);

            out_xblconfig = "xblconfig-" + name_suffix
            outfile_xblconfig = os.path.join(srcDir, out_xblconfig )

            print('Generating xblconfig')
            cmd = ['python', xblconfigtool_gen, '-i', outfile_json, '-fELF', '-o', outfile_xblconfig, '--tools_path', xblconfigtool_path, '--elf-address', '0x08CEE800', '-b', srcDir]
            print(cmd)
            prc = subprocess.Popen(cmd, cwd=cdir)
            prc.wait()
            if prc.returncode != 0:
                print('ERROR: unable to create xbl config')
                return prc.returncode

            outfile_xblconfig = os.path.join(srcDir,'raw', out_xblconfig + ".elf")

            #elf2mbn conversion
            bootconfig_path = cdir +'/scripts' + '/elftombn.py'
            print("Converting xbconfig elf to mbn ...")
            cmd = ['python', bootconfig_path, '-a', ARCH_NAME, '-f', outfile_xblconfig, '-o', cdir + "/" + out_xblconfig + ".elf", '-v', "7", '-s', "37"]
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

if __name__ == '__main__':
    main()
