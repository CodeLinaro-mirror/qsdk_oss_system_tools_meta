# ===========================================================================
# Copyright (c) 2024, Qualcomm Innovation Center, Inc. All rights reserved.
# SPDX-License-Identifier: ISC
# ===========================================================================

import xml.etree.ElementTree as ET
import itertools
import os
import subprocess
import sys
import glob
from getopt import getopt
from getopt import GetoptError

arch=""
flash="nor,tiny-nor,nand,norplusnand,emmc,norplusemmc"
ipq5424_supported_flash="nor,nand,norplusnand,emmc,norplusemmc,norplusemmc-gpt,norplusnand-gpt"
ipq5210_supported_flash="nor,nand,norplusnand,emmc,norplusemmc,norplusemmc-gpt,norplusnand-gpt"
ipq9650_supported_flash="nor,nand,norplusnand,emmc,norplusemmc,norplusemmc-gpt,norplusnand-gpt"
bootImgDir=""
rpmImgDir=""
tzImgDir=""
nhssImgDir=""
wififwImgDir=""

cdir = os.path.dirname(__file__)
cdir = os.path.abspath(cdir)
inDir = ""
dtcDir = ""
mode = ""

soc_dir = ""
attach1_dir = ""
attach2_dir = ""
attach3_dir = ""
attach4_dir = ""
attach5_dir = ""

## default mbn version
mbn_version = "3"

def print_help():
    print("\nUsage: python prepareSingleImage.py <option> <value>\n")

    print("--arch \t\tArch(e.g ipq40xx/ipq807x/ipq807x_64/ipq6018/ipq6018_64/ipq5018/ipq5018_64/ipq9574/ipq9574_64/ipq5332/ipq5332_64/ipq5424/ipq5424_64/ipq5210/ipq5210_64/ipq9650/ipq9650_64)\n")
    print(" \t\te.g python prepareSingleImage.py --arch ipq807x\n\n")

    print("--fltype \tFlash Type (nor/nand/emmc/norplusnand/norplusemmc)")
    print(" \t\tMultiple flashtypes can be passed by a comma separated string")
    print(" \t\tDefault is all. i.e If \"--fltype\" is not passed image for all the flash-type will be created.\n")
    print(" \t\te.g python prepareSingleImage.py --fltype nor,nand,norplusnand\n\n")

    print("--in \t\tGenerated binaries and images needed for singleimage will be copied to this location")
    print("\t\tDefault path: ./<ARCH>/in/\n")
    print("\t\te.g python prepareSingleImage.py --gencdt --in ./\n\n")

    print("--bootimg \tBoot image path")
    print("\t\tIf specified the boot images available at <PATH> will be copied to the directory provided with \"--in\"\n")
    print("\t\te.g python prepareSingleImage.py --bootimg <PATH>\n\n")

    print("--tzimg \tTZ image path")
    print("\t\tIf specified the TZ images available at <PATH> will be copied to the directory provided with \"--in\"\n")
    print("\t\te.g python prepareSingleImage.py --tzimg <PATH>\n\n")

    print("--nhssimg \tNHSS image path")
    print("\t\tIf specified the NHSS images available at <PATH> will be copied to the directory provided with \"--in\"\n")
    print("\t\te.g python prepareSingleImage.py --nhssimg <PATH>\n\n")

    print("--rpmimg \tRPM image path")
    print("\t\tIf specified the RPM images available at <PATH> will be copied to the directory provided with \"--in\"\n")
    print("\t\te.g python prepareSingleImage.py --rpmimg <PATH>\n\n")

    print("--gencdt \tWhether CDT binaries to be generated")
    print("\t\tIf not specified CDT binary will not be generated")
    print("\t\tThis Argument does not take any value\n")
    print("\t\te.g python prepareSingleImage.py --gencdt\n\n")

    print("--genxblcfg \tWhether xbl_config binaries to be generated")
    print("\t\tIf not specified xbl_config binary will not be generated")
    print("\t\tThis is currently used/needed only for IPQ5424")
    print("\t\tThis Argument does not take any value\n")
    print("\t\te.g python prepareSingleImage.py --genxblcfg\n\n")

    print("--genqccfg \tWhether qc_config binaries to be generated")
    print("\t\tIf not specified qc_config binary will not be generated")
    print("\t\tThis is currently used/needed only for IPQ5210/IPQ9650")
    print("\t\tThis Argument does not take any value\n")
    print("\t\te.g python prepareSingleImage.py --genqccfg\n\n")

    print("--dtc_path \tdtc binary path")
    print("\t\tThis option can be used with '--genxblcfg' and '--genqccfg'\n")
    print("\t\te.g python prepareSingleImage.py --genxblcfg --dtc_path /usr/bin\n\n")
    print("\t\te.g python prepareSingleImage.py --genqccfg --dtc_path /usr/bin\n\n")

    print("--genmelf \tWhether merged elf of xbl_sc and tme-l patch to be generated")
    print("\t\tIf not specified merged elf will not be generated")
    print("\t\tThis is currently used/needed only for IPQ5424/IPQ5210/IPQ9650")
    print("\t\tThis Argument does not take any value\n")
    print("\t\te.g python prepareSingleImage.py --genmelf\n\n")

    print("--memory \tWhether to use Low Memory Profiles for cdt binaries to be generated")
    print("\t\tThis option depends on '--gencdt'\n")
    print("\t\tIf specified the <VALUE> is taken as memory size in generating cdt binaries\n")
    print("\t\te.g python prepareSingleImage.py --gencdt --memory <VALUE>\n\n")

    print("--genpart \tWhether flash partition table(s) to be generated")
    print("\t\tIf not specified partition table(s) will not be generated")
    print("\t\tThis Argument does not take any value\n")
    print("\t\te.g python prepareSingleImage.py --genpart\n\n")

    print("--genbootconf \tWhether bootconfig binaries to be generated")
    print("\t\tIf not specified bootconfig binaries will not be generated")
    print("\t\tThis Argument does not take any value\n")
    print("\t\te.g python prepareSingleImage.py --genbootconf\n\n")

    print("--genmbn \tWhether u-boot.elf to be converted to u-boot.mbn")
    print("\t\tIf not specified u-boot.mbn will not be generated")
    print("\t\tThis is currently used/needed only for IPQ807x, IPQ6018, IPQ5018, IPQ9574, IPQ5332, IPQ5424, IPQ5210, IPQ9650")
    print("\t\tThis Argument does not take any value\n")
    print("\t\te.g python prepareSingleImage.py --genmbn\n\n")

    print("--lk \t\tWhether lkboot.elf to be converted to lkboot.mbn")
    print("\t\tIf not specified lkboot.mbn will not be generated")
    print("\t\tThis is currently used/needed only for IPQ807x")
    print("\t\tThis Argument does not take any value")
    print("\t\tThis option depends on '--genmbn'\n")
    print("\t\te.g python prepareSingleImage.py --genmbn --lk\n\n")

    print("--gentfambn \t\tWhether tfa elf to be converted to mbn")
    print("\t\tIf not specified tfa mbn will not be generated")
    print("\t\tThis is currently used/needed only for IPQ5210, IPQ9650")
    print("\t\tThis Argument does not take any value")
    print("\t\te.g python prepareSingleImage.py --gentfambn\n\n")

    print("--genopteembn \t\tWhether optee bin to be converted to mbn")
    print("\t\tIf not specified optee mbn will not be generated")
    print("\t\tThis is currently used/needed only for IPQ5210, IPQ9650")
    print("\t\tAuto-generates single-segment ELF from .bin files with chipset load addresses")
    print("\t\tThis Argument does not take any value")
    print("\t\te.g python prepareSingleImage.py --genopteembn\n\n")

    print("--genbootldr \tWhether bootldr binaries to be generated")
    print("\t\tIf not specified bootldr binaries will not be generated")
    print("\t\tThis Argument does not take any value\n")
    print("\t\te.g python prepareSingleImage.py --genbootldr\n\n")

    print("--genlicense \tWhether license blob must be generated")
    print("\t\tIf not specified license binaries will not be generated")
    print("\t\tThis argument will not take any values itself but it should be added in SOCs and attaches")
    print("\t\t*.pfm files are used to generate the License blob from given path and flash specific\n")
    print("\t\te.g python prepareSingleImage.py --genlicense --soc ./license --attach1 ./attach_license\n\n")

    print("--total_blocks \tTotal blocks\n\n")
    print("--flash_size \tFlash size")
    print("--help \t\tPrint This Message\n\n")

    print("\t\t\t\t <<<<<<<<<<<<< A Sample Run >>>>>>>>>>>>>\n")
    print("python prepareSingleImage.py --arch ipq40xx --fltype nor,nand,norplusnand --gencdt --genxblcfg --genbootconf --genpart --in ./in_put/\n\n\n")


def copy_images(image_type, build_dir):
    global arch
    global configDir

    tree = ET.parse(configDir)
    root = tree.getroot()

    entries = root.findall("./data[@type='COPY_IMAGES']/image[@type='" + image_type + "']/entry")
    for entry in entries:
        image_path = entry.find(".//image_path")
        image_path.text = build_dir.rstrip() + image_path.text
        print("image_path.text:" + image_path.text)
        print("cp " + image_path.text  + " " + inDir)
        os.system("cp " + image_path.text  + " " + inDir)

def gen_cdt():
    global srcDir
    global configDir
    global memory

    cdt_path = srcDir + '/gen_cdt_bin.py'
    prc = subprocess.Popen(['python', cdt_path, '-c', configDir, '-o', inDir, '-m', memory], cwd=cdir)
    prc.wait()

    if prc.returncode != 0:
        print('ERROR: unable to create CDT binary')
        return prc.returncode

    if arch not in ["ipq807x", "ipq807x_64", "ipq6018", "ipq6018_64", "ipq5018", "ipq5018_64", "ipq9574", "ipq9574_64", "ipq5332", "ipq5332_64"]:
        return 0

    ipq_xml_path = inDir + "/" + arch
    data_retention_cdt_path = cdir + "/data_retention_cdt"
    data_retention_cdt_configDir = data_retention_cdt_path + "/" + arch + "/config.xml"
    if not os.path.exists(data_retention_cdt_path):
        os.makedirs(data_retention_cdt_path)
        copy_cmd = "cp -rf " + ipq_xml_path + " " + data_retention_cdt_path
        os.system(copy_cmd)
        sed_cmd = "sed -i.bak -e 's/<data_retention>false<\/data_retention>/<data_retention>true<\/data_retention>/' " + data_retention_cdt_configDir
        os.system(sed_cmd)

    prc = subprocess.Popen(['python', cdt_path, '-c', data_retention_cdt_configDir, '-o', data_retention_cdt_path, '-m', memory], cwd=cdir)
    prc.wait()

    if prc.returncode != 0:
        print('ERROR: unable to create CDT binary')
        return prc.returncode

    return 0

def gen_xblcfg():
    global srcDir
    global configDir
    global memory
    global dtcDir

    xblconfig_path = srcDir + '/gen_xblconfig_bin.py'
    data_retention_xblcfg_path = cdir + "/data_retention_xblcfg"

    if not os.path.exists(data_retention_xblcfg_path):
        dts_file_path = cdir + "/" + arch + "/xbl_config/*"
        sed_cmd = "sed -i.bak -e 's/ddr_retention_en = <0>/ddr_retention_en = <1>/g' " + dts_file_path
        os.system(sed_cmd)

        prc = subprocess.Popen(['python', xblconfig_path, '-c', configDir, '-o', inDir, '-m', memory, '--dtc_path', dtcDir], cwd=cdir)
        prc.wait()

        if prc.returncode != 0:
            print('ERROR: unable to create xbl_config binary')
            return prc.returncode

        os.makedirs(data_retention_xblcfg_path)
        copy_cmd = "cp -rf " + cdir + "/xblconfig-* " + data_retention_xblcfg_path
        os.system(copy_cmd)

        sed_cmd = "sed -i.bak -e 's/ddr_retention_en = <1>/ddr_retention_en = <0>/g' " + dts_file_path
        os.system(sed_cmd)

    prc = subprocess.Popen(['python', xblconfig_path, '-c', configDir, '-o', inDir, '-m', memory, '--dtc_path', dtcDir], cwd=cdir)
    prc.wait()

    if prc.returncode != 0:
        print('ERROR: unable to create xbl_config binary')
        return prc.returncode
    return 0

def gen_qccfg():
    global srcDir
    global configDir
    global memory
    global dtcDir

    xblconfig_path = srcDir + '/gen_xblconfig_bin.py'
    data_retention_qccfg_path = cdir + "/data_retention_qccfg"

    if not os.path.exists(data_retention_qccfg_path):
        dts_file_path = cdir + "/" + arch + "/qc_config/*"
        sed_cmd = "sed -i.bak -e 's/ddr_retention_en = <0>/ddr_retention_en = <1>/g' " + dts_file_path
        ret = os.system(sed_cmd)
        if ret != 0:
            print('ERROR: unable to modify dts files for data retention')
            return -1

        prc = subprocess.Popen(['python', xblconfig_path, '-c', configDir, '-o', inDir, '-m', memory, '--dtc_path', dtcDir, '--genqccfg'], cwd=cdir)
        prc.wait()

        if prc.returncode != 0:
            print('ERROR: unable to create qc_config binary')
            return prc.returncode

        try:
            os.makedirs(data_retention_qccfg_path)
        except OSError as e:
            print('ERROR: unable to create directory {0}: {1}'.format(data_retention_qccfg_path, e))
            return -1

        copy_cmd = "cp -rf " + cdir + "/qcconfig-* " + data_retention_qccfg_path
        ret = os.system(copy_cmd)
        if ret != 0:
            print('ERROR: unable to copy qcconfig files')
            return -1

        sed_cmd = "sed -i.bak -e 's/ddr_retention_en = <1>/ddr_retention_en = <0>/g' " + dts_file_path
        ret = os.system(sed_cmd)
        if ret != 0:
            print('ERROR: unable to restore dts files')
            return -1

    prc = subprocess.Popen(['python', xblconfig_path, '-c', configDir, '-o', inDir, '-m', memory, '--dtc_path', dtcDir, '--genqccfg'], cwd=cdir)
    prc.wait()

    if prc.returncode != 0:
        print('ERROR: unable to create qc_config binary')
        return prc.returncode
    return 0

def has_null_program_headers(file_path):
    """
    Check if an ELF file has NULL program headers.
    MBN files renamed to .elf have NULL program headers, ELF files will be preserved.
    Args:
        file_path: Path to the file to check
    Returns:
        True if file has NULL program headers (is MBN),
        False if not (is ELF),
        None on error
    """
    if not os.path.exists(file_path):
        return None

    try:
        # Use readelf to check for NULL program headers
        cmd = "readelf -l %s 2>&1" % file_path
        prc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, err = prc.communicate()

        if prc.returncode != 0:
            # readelf failed - might not be ELF format at all
            return None

        if sys.version_info.major >= 3:
            output = output.decode("utf-8")

        # Check if output contains NULL program headers
        # MBN files have NULL program headers, true ELF files have LOAD headers
        has_null = 'NULL' in output and 'Type' in output
        return has_null

    except Exception as e:
        print('ERROR: Unable to check program headers for %s: %s' % (file_path, str(e)))
        return None

def process_qclib_files():
    """
    Process QCLib.elf and QCLib_flashless.elf files.

    Check if these files are MBN (with NULL headers) or true ELF files:
    - If MBN: Simply rename from .elf to .mbn
    - If ELF: Convert to MBN using elftombn.py and save as .mbn

    Returns:
        0 on success, non-zero on failure
    """
    global srcDir
    global cdir
    global mbn_version
    global arch
    global inDir

    # List of QCLib files to process
    qclib_files = ['QCLib.elf', 'QCLib_flashless.elf']

    bootconfig_path = srcDir + '/elftombn.py'

    for qclib_file in qclib_files:
        elf_path = inDir + "/" + qclib_file
        mbn_path = inDir + "/" + qclib_file.replace('.elf', '.mbn')

        # Skip if file doesn't exist
        if not os.path.exists(elf_path):
            print('Note: %s not found, skipping' % qclib_file)
            continue

        # Check if file has NULL program headers
        has_null_headers = has_null_program_headers(elf_path)

        if has_null_headers is None:
            print('ERROR: Unable to determine format of %s' % qclib_file)
            return -1
        elif has_null_headers:
            # File is MBN - renamed from .elf to .mbn
            print('%s is already in MBN format, copying to .mbn' % qclib_file)
            try:
                with open(elf_path, 'rb') as src:
                    with open(mbn_path, 'wb') as dst:
                        dst.write(src.read())
                print('Successfully copied %s to %s' % (qclib_file, qclib_file.replace('.elf', '.mbn')))
            except (OSError, IOError) as e:
                print('ERROR: Unable to copy %s: %s' % (qclib_file, str(e)))
                return -1
        else:
            # File is true ELF - convert to MBN
            print('%s is ELF format, converting to MBN' % qclib_file)
            prc = subprocess.Popen(['python', bootconfig_path, '-a', arch, '-f', elf_path, '-o', mbn_path, '-v', mbn_version, '-s', '0'], cwd=cdir)
            prc.wait()

            if prc.returncode != 0:
                print('ERROR: Unable to convert %s from ELF to MBN' % qclib_file)
                return prc.returncode

            print('Successfully converted %s to %s' % (qclib_file, qclib_file.replace('.elf', '.mbn')))

    return 0

def gen_melf():
    global srcDir
    global configDir
    global memory
    global dtcDir
    global arch

    # Check if this is IPQ5424 chipset (only IPQ5424 uses xbl_sc.elf)
    if arch == "ipq5424" or arch == "ipq5424_64":
        # IPQ5424: Use xbl_sc.elf with multiple variants
        xbl_img_dict = {'xbl_sc.elf'           : 'xbl_s.melf',
                        'xbl_sc_atf.elf'       : 'xbl_s_atf.melf',
                        'xbl_sc_flashless.elf' : 'xbl_s_flashless.melf',
                        'xbl_sc_devprg.elf'    : 'xbl_s_devprg.melf'}

        # create melf
        script_path = inDir + '/create_multielf.py'
        for xbl_elf, xbl_melf in xbl_img_dict.items():
            # XBL ATF is optional, skip if not present in input directory
            if 'atf' in xbl_elf and os.path.isfile(inDir+"/"+xbl_elf) == False:
                print('Optional image - xbl_sc_atf.elf file not present, skipping xbl_s_atf.melf binary')
            else:
                prc = subprocess.Popen(['python', script_path, '-f', inDir+"/"+xbl_elf+","+ inDir+"/tmel-ipq54xx-patch.elf", '-o', inDir+"/"+xbl_melf], cwd=cdir)
                prc.wait()
                if prc.returncode != 0:
                    print('ERROR: unable to create xbl_s.melf binary')
                    return prc.returncode

        # create nand melf
        script_path = inDir + '/Gen_xbl_nand_elf.py'
        xbl_nand_input_img_list = ['xbl_s.melf', 'xbl_s_atf.melf']
        xbl_nand_cmd_list       = ['NAND_2K', 'NAND_4K']

        # Generate XBL 2K and 4K nand images
        for xbl_nand_cmd in xbl_nand_cmd_list:
            for xbl_nand_input_img in xbl_nand_input_img_list:
                # Get output image name
                if xbl_nand_cmd == 'NAND_2K':
                    xbl_nand_output_img = xbl_nand_input_img.replace('xbl_s', 'xbl_s_nand')
                    xbl_nand_intermediate = 'xbl_nand.elf'
                else:
                    xbl_nand_output_img = xbl_nand_input_img.replace('xbl_s', 'xbl_s_nand_4K')
                    xbl_nand_intermediate = 'xbl_nand_4K.elf'

                # XBL ATF is optional, skip if not present in input directory
                if 'atf' in xbl_nand_input_img and os.path.isfile(inDir+"/"+xbl_nand_input_img) == False:
                    print('skipping '+xbl_nand_output_img+' binary')
                else:
                    # create NAND melf
                    prc = subprocess.Popen(['python',script_path, inDir+"/"+xbl_nand_input_img, '-f', xbl_nand_cmd,'-o', inDir ], cwd=cdir)
                    prc.wait()
                    if prc.returncode != 0:
                        print('ERROR: unable to create '+xbl_nand_output_img+' binary')
                        return prc.returncode
                    else:
                        os.rename(os.path.join(inDir, xbl_nand_intermediate), os.path.join(inDir, xbl_nand_output_img));
    else:
        # IPQ5210, IPQ9650 and other chipsets: Use u-boot-spl.mbn
        # Dict: input_file -> (output_melf, is_optional)
        # u-boot-spl.mbn QCLib_flashless.elf is required
        spl_img_dict = {
            'u-boot-spl.mbn'     : ('u-boot-spl.melf',     False),
            'QCLib_flashless.mbn': ('QCLib_flashless.melf', False),
        }

        # Check if u-boot-spl.mbn exists (required)
        if not os.path.isfile(inDir+"/u-boot-spl.mbn"):
            print('ERROR: u-boot-spl.mbn file not present in input directory')
            return -1

        # Determine TME patch file based on architecture
        # Map architecture to TME patch file naming convention
        tme_patch_map = {
            'ipq5210': 'tmel-ipq52xx-patch.elf',
            'ipq5210_64': 'tmel-ipq52xx-patch.elf',
            'ipq9650': 'tmel-ipq96xx-patch.elf',
            'ipq9650_64': 'tmel-ipq96xx-patch.elf',
            # Add more architectures here as needed
        }

        tme_patch_file = tme_patch_map.get(arch, None)

        if not tme_patch_file:
            print('ERROR: No TME patch file mapping defined for architecture: ' + arch)
            return -1

        if not os.path.isfile(inDir+"/"+tme_patch_file):
            print('ERROR: TME patch file not present in input directory: ' + tme_patch_file)
            return -1

        # create melf for each input file
        script_path = inDir + '/create_multielf.py'

        for input_img, (output_melf, is_optional) in spl_img_dict.items():
            if is_optional and not os.path.isfile(inDir+"/"+input_img):
                print('Optional image - '+input_img+' file not present, skipping '+output_melf+' binary')
                continue
            print('Creating '+output_melf+' from '+input_img+' with TME patch: ' + tme_patch_file)
            prc = subprocess.Popen(['python', script_path, '-f', inDir+"/"+input_img+","+ inDir+"/"+tme_patch_file, '-o', inDir+"/"+output_melf], cwd=cdir)
            prc.wait()
            if prc.returncode != 0:
                print('ERROR: unable to create '+output_melf+' binary')
                return prc.returncode

        # NAND images are generated only for u-boot-spl.melf
        nand_input_img_list = ['u-boot-spl.melf']

        # create nand melf for each generated melf
        script_path = inDir + '/Gen_xbl_nand_elf.py'
        nand_cmd_list = ['NAND_2K', 'NAND_4K']

        for nand_cmd in nand_cmd_list:
            for nand_input_img in nand_input_img_list:
                # Get output image name and intermediate file name
                base_name = nand_input_img.replace('.melf', '')
                if nand_cmd == 'NAND_2K':
                    nand_output_img = base_name + '_nand.melf'
                    nand_intermediate = 'xbl_nand.elf'
                else:
                    nand_output_img = base_name + '_nand_4K.melf'
                    nand_intermediate = 'xbl_nand_4K.elf'

                print('Creating '+nand_output_img+' from '+nand_input_img)
                prc = subprocess.Popen(['python', script_path, inDir+"/"+nand_input_img, '-f', nand_cmd, '-o', inDir], cwd=cdir)
                prc.wait()
                if prc.returncode != 0:
                    print('ERROR: unable to create '+nand_output_img+' binary')
                    return prc.returncode
                else:
                    if os.path.exists(os.path.join(inDir, nand_intermediate)):
                        os.rename(os.path.join(inDir, nand_intermediate), os.path.join(inDir, nand_output_img))

    return 0

def gen_part(flash):
    global srcDir
    global configDir
    global flash_size
    global total_blocks

    flash_partition_path = srcDir + '/gen_flash_partition_bin.py'
    for flash_type in flash.split(","):
        prc = subprocess.Popen(['python', flash_partition_path, '-c', configDir, '-f', flash_type, '-o', inDir, '-s', flash_size, '-t', total_blocks], cwd=cdir)
        prc.wait()

        if prc.returncode != 0:
            print('ERROR: unable to generate partition table for ' + flash_type)
            return prc.returncode
    return 0

def gen_bootconfig(flag):
    global srcDir
    global configDir

    if arch not in ["ipq40xx", "ipq806x", "ipq807x", "ipq807x_64", "ipq6018", "ipq6018_64", "ipq5018", "ipq5018_64", "ipq9574", "ipq9574_64", "ipq5332", "ipq5332_64"]:
        print("Invalid arch type: " + arch)
        return -1

    bootconfig_path = srcDir + '/gen_bootconfig_bin.py'
    print("Creating Bootconfig")
    if(flag == 0):
        prc = subprocess.Popen(['python', bootconfig_path, '-c', configDir, '-o', inDir], cwd=cdir)
    if(flag == 1):
        prc = subprocess.Popen(['python', bootconfig_path, '-c', configDir, '-o', inDir, '-f', 'crc', ], cwd=cdir)
    prc.wait()

    if prc.returncode != 0:
        print('ERROR: unable to create bootconfig binary')
        return prc.returncode
    return 0

def gen_bootldr():
    global srcDir
    global configDir
    global memory

    bootldr_path = srcDir + '/gen_bootldr_bin.py'
    print("Creating bootldr")
    prc = subprocess.Popen(['python', bootldr_path, '-c', configDir, '-o', inDir, '-m', memory], cwd=cdir)
    prc.wait()

    if prc.returncode != 0:
        print('ERROR: unable to create bootldr binary')
        return prc.returncode
    return 0

def gen_license():
    global cdir
    global soc_dir
    global attach1_dir
    global attach2_dir
    global attach3_dir
    global attach4_dir
    global attach5_dir
    global flash
    global arch
    global mode

    for type in flash.split(","):
        if arch == "ipq5424":
            prc = subprocess.Popen(['python', srcDir + '/gen_license.py', '--arch',
                arch, '--fltype', type, '--in', cdir, '--soc', soc_dir])
        else:
            prc = subprocess.Popen(['python', srcDir + '/gen_license.py', '--arch',
                arch, '--fltype', type, '--in', cdir, '--soc', soc_dir,
                '--attach1', attach1_dir, '--attach2', attach2_dir, '--attach3',
                attach3_dir, '--attach4', attach4_dir, '--attach5', attach5_dir])
        prc.wait()

        if prc.returncode != 0:
            print('ERROR: Generating license bin')
            return prc.returncode

    return 0

def gen_mbn():
    global srcDir
    global mbn_version
    global arch

    bootconfig_path = srcDir + '/elftombn.py'
    print("Converting u-boot elf to mbn ...")
    u_boot_2016_path=inDir + "/openwrt-" + arch + "-u-boot.elf"
    u_boot_spl_path=inDir + "/u-boot-spl.elf"
    tiny_path=inDir + "/openwrt-" + arch + "_tiny" + "-u-boot.elf"
    tiny_nor_path=inDir + "/openwrt-" + arch + "_tiny_nor" + "-u-boot.elf"
    img_flag = 1

    if mode == "32":
        img_str = "-" + arch[:-2]+"xx_32-"
        img_path = [inDir + "/openwrt-" + arch + img_str + "mmc32" + "-u-boot.elf", \
                inDir + "/openwrt-" + arch + img_str + "norplusmmc32" + "-u-boot.elf", \
                inDir + "/openwrt-" + arch + img_str + "nand32" + "-u-boot.elf", \
                inDir + "/openwrt-" + arch + img_str + "norplusnand32" + "-u-boot.elf", \
                inDir + "/openwrt-" + arch + img_str + "tiny_nand32" + "-u-boot.elf", \
                inDir + "/openwrt-" + arch + img_str + "tiny_v2_nand32" + "-u-boot.elf", \
                inDir + "/openwrt-" + arch + img_str + "tiny_nand32_64M" + "-u-boot.elf", \
                inDir + "/openwrt-" + arch + img_str + "tiny_v2_nand32_64M" + "-u-boot.elf", \
                inDir + "/openwrt-" + arch + img_str + "tiny_nor32" + "-u-boot.elf", \
                inDir + "/openwrt-" + arch + img_str + "tiny_norplusnand32" + "-u-boot.elf", \
                inDir + "/openwrt-" + arch + img_str + "tiny_v2_norplusnand32" + "-u-boot.elf", \
                inDir + "/openwrt-" + arch + img_str + "mmc32" + "-u-boot_signed.mbn", \
                inDir + "/openwrt-" + arch + img_str + "norplusmmc32" + "-u-boot_signed.mbn", \
                inDir + "/openwrt-" + arch + img_str + "nand32" + "-u-boot_signed.mbn", \
                inDir + "/openwrt-" + arch + img_str + "norplusnand32" + "-u-boot_signed.mbn"]
        for fname in glob.glob(inDir + "/openwrt-" + arch + img_str + "*-u-boot-*.elf"):
            if "stripped" in fname or "unstripped" in fname or "wrapped" in fname or "spl" in fname:
                continue
            img_path.append(fname)

    elif mode == "64":
        img_str = "-generic-"
        img_path = [inDir + "/openwrt-" + arch + img_str + "mmc" + "-u-boot.elf", \
                inDir + "/openwrt-" + arch + img_str + "norplusmmc" + "-u-boot.elf", \
                inDir + "/openwrt-" + arch + img_str + "nand" + "-u-boot.elf", \
                inDir + "/openwrt-" + arch + img_str + "norplusnand" + "-u-boot.elf", \
                inDir + "/openwrt-" + arch + img_str + "mmc" + "-u-boot_signed.mbn", \
                inDir + "/openwrt-" + arch + img_str + "norplusmmc" + "-u-boot_signed.mbn", \
                inDir + "/openwrt-" + arch + img_str + "nand" + "-u-boot_signed.mbn", \
                inDir + "/openwrt-" + arch + img_str + "norplusnand" + "-u-boot_signed.mbn"]

        for fname in glob.glob(inDir + "/openwrt-" + arch + img_str + "*-u-boot-*.elf"):
            if "stripped" in fname or "unstripped" in fname or "wrapped" in fname or "spl" in fname:
                continue
            img_path.append(fname)

    if mbn_version == "3":
        if os.path.exists(u_boot_2016_path):
            prc = subprocess.Popen(['python', bootconfig_path, '-f', inDir + "/openwrt-" +  arch + "-u-boot.elf", '-o', inDir + "/openwrt-" + arch + "-u-boot.mbn"], cwd=cdir)
            img_flag = 0

        for img in img_path:
            if os.path.exists(img):
                if "signed" not in img:
                    subprocess.call(['python', bootconfig_path, '-a', arch, '-f', img, '-o', img[:-3] + "mbn", '-v', "6"], cwd=cdir)
                cmd = 'objcopy -I binary -O elf32-i386 --binary-architecture i386 %s %s' % (img[:-4] + ".mbn", img[:-4] + "_out.o")
                subprocess.call(cmd, shell=True)
                cmd = 'ld -m elf_i386 %s -T %s  -o  %s' % (img[:-4] + "_out.o", inDir + "/uboot.ld", img[:-4] + "_wrapped.elf")
                subprocess.call(cmd, shell=True)
                subprocess.call(['python', bootconfig_path, '-a', arch, '-f', img[:-4] + "_wrapped.elf", '-o', img[:-4] + "_compressed.mbn", '-v', "6", '-c', "lzma"], cwd=cdir)
                img_flag = 0

        if os.path.exists(tiny_path):
            prc = subprocess.Popen(['python', bootconfig_path, '-f', inDir + "/openwrt-" + arch + "_tiny" + "-u-boot.elf", '-o', inDir + "/openwrt-" + arch + "_tiny" + "-u-boot.mbn"], cwd=cdir)
            img_flag = 0

        if os.path.exists(tiny_nor_path):
            prc = subprocess.Popen(['python', bootconfig_path, '-f', inDir + "/openwrt-" + arch + "_tiny_nor" + "-u-boot.elf", '-o', inDir + "/openwrt-" + arch + "_tiny_nor" + "-u-boot.mbn"], cwd=cdir)

    else:
        if os.path.exists(u_boot_2016_path):
            prc = subprocess.Popen(['python', bootconfig_path, '-a', arch, '-f', inDir + "/openwrt-" + arch + "-u-boot.elf", '-o', inDir + "/openwrt-" + arch + "-u-boot.mbn", '-v', "6"], cwd=cdir)
            img_flag = 0

        for img in img_path:
            if os.path.exists(img):
                cmd = "readelf -h %s | grep Entry | awk -F ' ' '{print $4}'" % img
                prc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
                entry_point, err = prc.communicate()
                if err != None:
                    print("Failed to parse entry point from %s", img)
                    return -1

                if sys.version_info.major >= 3:
                    entry_point = entry_point.decode("utf-8").strip()

                entry_point = entry_point.strip()

                cmd = 'echo "SECTIONS { . = %s ; .data : { *(.data) } }" > %s' % (entry_point, inDir + "/uboot.ld")
                subprocess.call(cmd, shell=True)

                cmd = 'sed -i -e "s/4a280000/4a400000/g" %s' % (inDir + "/uboot.ld")
                subprocess.call(cmd, shell=True)
                cmd = 'sed -i -e "s/4a240000/4a400000/g" %s' % (inDir + "/uboot.ld")
                subprocess.call(cmd, shell=True)

                if "signed" not in img:
                    subprocess.call(['python', bootconfig_path, '-a', arch, '-f', img, '-o', img[:-3] + "mbn", '-v', mbn_version, '-s', "9"], cwd=cdir)
                cmd = 'objcopy -I binary -O elf32-i386 --binary-architecture i386 %s %s' % (img[:-4] + ".mbn", img[:-4] + "_out.o")
                subprocess.call(cmd, shell=True)
                cmd = 'ld -m elf_i386 %s -T %s  -o  %s' % (img[:-4] + "_out.o", inDir + "/uboot.ld", img[:-4] + "_wrapped.elf")
                subprocess.call(cmd, shell=True)
                subprocess.call(['python', bootconfig_path, '-a', arch, '-f', img[:-4] + "_wrapped.elf", '-o', img[:-4] + "_compressed.mbn", '-v', mbn_version, '-c', "lzma", '-s', "9"], cwd=cdir)
                img_flag = 0

        if os.path.exists(tiny_path):
            prc = subprocess.Popen(['python', bootconfig_path, '-a', arch, '-f', inDir + "/openwrt-" + arch + "_tiny" + "-u-boot.elf", '-o', inDir + "/openwrt-" + arch + "_tiny" + "-u-boot.mbn", '-v', "6"], cwd=cdir)
            img_flag = 0

        if os.path.exists(tiny_nor_path):
            prc = subprocess.Popen(['python', bootconfig_path, '-a', arch, '-f', inDir + "/openwrt-" + arch + "_tiny_nor" + "-u-boot.elf", '-o', inDir + "/openwrt-" + arch + "_tiny_nor" + "-u-boot.mbn", '-v', "6"], cwd=cdir)

        if os.path.exists(u_boot_spl_path):
            print("Converting u-boot-spl.elf to u-boot-spl.mbn ...")
            prc = subprocess.Popen(['python', bootconfig_path, '-a', arch, '-f', inDir + "/u-boot-spl.elf", '-o', inDir + "/u-boot-spl.mbn", '-v', mbn_version, '-s', "0"], cwd=cdir)
            img_flag = 0

    if(img_flag):
        print("u-boot image is not available")
        print("Failed to create mbn!")
        return -1

    if os.path.exists(u_boot_2016_path) or os.path.exists(tiny_path) or os.path.exists(u_boot_spl_path):
        prc.wait()

        if prc.returncode != 0:
            print('ERROR: unable to convert U-Boot .elf to .mbn')
            return prc.returncode

    print("U-Boot .mbn file is created")

    # Process QCLib files (convert/rename .elf to .mbn) for ipq5210 and ipq9650
    if arch == "ipq5210" or arch == "ipq9650":
        if process_qclib_files() != 0:
            return -1

    return 0

def gen_lk_mbn():
    global srcDir

    bootconfig_path = srcDir + '/elftombn.py'
    print("Converting LK elf to mbn ...")
    if mbn_version == "3":
        prc = subprocess.Popen(['python', bootconfig_path, '-f', inDir + "/openwrt-" + arch + "-lkboot.elf", '-o', inDir + "/openwrt-" + arch + "-lkboot.mbn"], cwd=cdir)
    else:
        prc = subprocess.Popen(['python', bootconfig_path, '-f', inDir + "/openwrt-" + arch + "-lkboot.elf", '-o', inDir + "/openwrt-" + arch + "-lkboot.mbn", '-v', "6"], cwd=cdir)
    prc.wait()

    if prc.returncode != 0:
        print('ERROR: unable to convert LK .elf to .mbn')
        return prc.returncode
    else:
        print("LK .mbn file is created")
        return 0

def gen_tfa_mbn():
    global srcDir

    bootconfig_path = srcDir + '/elftombn.py'
    print("Converting TF-A elf to mbn ...")
    prc = subprocess.Popen(['python', bootconfig_path, '-f', inDir + "/bl31.elf", '-o', inDir + "/bl31.mbn", '-v', "7", '-s', "30"], cwd=cdir)
    prc.wait()

    if prc.returncode != 0:
        print('ERROR: Unable to convert TF-A .elf to .mbn')
        return prc.returncode
    else:
        print("TF-A .mbn file is created")
        return 0

def gen_optee_mbn():
    global srcDir
    global inDir

    tee_elf_path = inDir + "/tee.elf"

    if not os.path.exists(tee_elf_path):
        print("ERROR: tee.elf not found in " + inDir)
        return -1

    print("Found tee.elf, extracting entry point...")
    cmd = "readelf -h %s | grep Entry | awk -F ' ' '{print $4}'" % tee_elf_path
    prc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    entry_point, err = prc.communicate()
    if err is not None:
        print("ERROR: Failed to parse entry point from tee.elf")
        return -1

    if sys.version_info.major >= 3:
        entry_point = entry_point.decode("utf-8").strip()
    load_address = entry_point.strip()
    print("Using entry point from tee.elf: " + load_address)

    # Check for .bin files and generate corresponding .elf files
    bin_files = ['tee-raw.bin', 'tee-raw_lm.bin']

    for bin_file in bin_files:
        bin_path = inDir + "/" + bin_file

        if os.path.exists(bin_path):
            print("Found " + bin_file + ", generating single segment ELF...")

            # Create linker script content
            ld_content = """ENTRY(_entry)
SECTIONS
{
    . = %s;

    _entry = . ;

    .data : {
        *(.data)
    }
}
""" % load_address

            # Write linker script to file
            ld_file = inDir + "/optee-" + bin_file.replace('.bin', '.ld')
            try:
                with open(ld_file, 'w') as f:
                    f.write(ld_content)
                print("Created linker script: " + ld_file)
            except IOError as e:
                print("ERROR: Failed to create linker script: " + str(e))
                continue

            obj_file = inDir + "/" + bin_file.replace('.bin', '_out.o')
            elf_file_name = bin_file.replace('.bin', '.elf')
            elf_path = inDir + "/" + elf_file_name

            cmd = ['objcopy', '-I', 'binary', '-O', 'elf64-x86-64', '--binary-architecture', 'i386:x86-64', bin_path, obj_file]
            ret = subprocess.call(cmd)
            if ret != 0:
                print("ERROR: Failed to convert " + bin_file + " to object file")
                return -1

            cmd = ['ld', '-m', 'elf_x86_64', obj_file, '-T', ld_file, '-o', elf_path]
            ret = subprocess.call(cmd)
            if ret != 0:
                print("ERROR: Failed to link " + elf_file_name)
                return -1

            print("Successfully created " + elf_file_name + " from " + bin_file)

    bootconfig_path = srcDir + '/elftombn.py'
    print("Converting OPTEE elf to mbn ...")

    optee_files = ['tee-raw.elf', 'tee-raw_lm.elf']

    for elf_file in optee_files:
        elf_path = inDir + "/" + elf_file
        mbn_path = inDir + "/" + elf_file.replace('.elf', '.mbn')

        if os.path.exists(elf_path):
            prc = subprocess.Popen(['python', bootconfig_path, '-f', elf_path, '-o', mbn_path, '-v', "7", '-s', "204"], cwd=cdir)
            prc.wait()

            if prc.returncode != 0:
                print('WARNING: Unable to convert ' + elf_file + ' to .mbn')
            else:
                print("Converted " + elf_file.replace('.elf', '.mbn'))
        else:
            print("Skipping " + elf_file)

    return 0

def cleanup_intermediate_files():
    """Clean up intermediate files generated during the build process.

    This function removes temp files that are not needed after MBN and MELF
    files have been created. These intermediate files include hash, object,
    wrapped ELF files, and other temp build artifacts.
    """
    global inDir

    print("\nCleaning up intermediate files...")

    # Define patterns for files to delete
    cleanup_patterns = [
        "*.hash",           # Hash files (144 bytes each)
        "*_hash.hd",        # Hash header files (64 bytes each)
        "*_combined_hash.mbn",  # Combined hash MBN files (208 bytes each)
        "*_phdr.pbn",       # Program header binary files
        "*_out.o",          # Object files from objcopy (~900KB+ each)
        "*_wrapped.elf",    # Wrapped ELF files from linker (~900KB+ each)
        "*.ld",             # Temporary linker script
        "comfile0",         # Uncompressed intermediate file
        "comfile0.lzma",    # LZMA compressed intermediate file
        "*.bak"             # Backup files from sed operations
    ]

    deleted_count = 0

    for pattern in cleanup_patterns:
        file_pattern = os.path.join(inDir, pattern)
        matching_files = glob.glob(file_pattern)

        for file_path in matching_files:
            try:
                # Get file size before deletion for reporting
                file_size = os.path.getsize(file_path)
                os.remove(file_path)
                deleted_count += 1
                print("Deleted: %s (%d bytes)" % (os.path.basename(file_path), file_size))
            except OSError as e:
                print("Warning: Could not delete %s: %s" % (file_path, str(e)))

    print("\nCleanup complete:")
    print("  Files deleted: %d" % deleted_count)

    return 0

def main():
    global flash
    global arch
    global bootImgDir
    global tzImgDir
    global nhssImgDir
    global rpmImgDir
    global wififwImgDir
    global srcDir
    global configDir
    global inDir
    global dtcDir
    global mode
    global mbn_version
    global memory
    global flash_size
    global total_blocks
    global soc_dir
    global attach1_dir
    global attach2_dir
    global attach3_dir
    global attach4_dir
    global attach5_dir

    to_generate_cdt = "false"
    to_generate_xblcfg = "false"
    to_generate_qccfg = "false"
    to_generate_melf = "false"
    to_generate_part = "false"
    to_generate_bootconf = "false"
    to_generate_bootconf_crc = "false"
    to_generate_mbn = "false"
    to_generate_lk_mbn = "false"
    to_gen_tfa_mbn = "false"
    to_gen_optee_mbn = "false"
    to_generate_bootldr = "false"
    to_generate_license = "false"
    memory = "default"
    flash_size = ""
    total_blocks = ""
    lic_dir = ""

    if len(sys.argv) > 1:
        try:
            opts, args = getopt(sys.argv[1:], "h", ["arch=", "fltype=", "in=",
                "bootimg=", "tzimg=", "nhssimg=", "rpmimg=", "wififwimg",
                "gencdt", "genxblcfg", "genqccfg", "genmelf", "dtc_path=","memory=",
                "total_blocks=", "flash_size=", "genpart", "genbootconf", "genbootconf_crc",
                "genmbn", "lk", "genbootldr", "genlicense", "gentfambn", "genopteembn", "soc=","attach1=",
		"attach2=", "attach3=", "attach4=", "attach5=", "help"])
        except GetoptError as e:
            print_help()
            raise

        for option, value in opts:
            if option == "--arch":
                arch = value
                if arch not in ["ipq40xx", "ipq806x", "ipq807x", "ipq807x_64", "ipq6018", "ipq6018_64", "ipq5018", "ipq5018_64", "ipq9574", "ipq9574_64", "ipq5332", "ipq5332_64", "ipq5424", "ipq5424_64", "ipq5210", "ipq5210_64", "ipq9650", "ipq9650_64"]:
                    print("Invalid arch type: " + arch)
                    print_help()
                    return -1
                if arch == "ipq807x" or arch == "ipq5018" or arch == "ipq9574" or arch == "ipq5332" or arch == "ipq5424" or arch == "ipq5210" or arch == "ipq9650":
                    mode = "32"
                elif arch == "ipq807x_64" or arch == "ipq5018_64" or arch == "ipq9574_64" or arch == "ipq5332_64" or arch == "ipq5424_64" or arch == "ipq5210_64" or arch == "ipq9650_64":
                    mode = "64"
                    arch = arch[:-3]

                if arch == "ipq6018":
                    mode = "32"
                elif arch == "ipq6018_64":
                    mode = "64"
                    arch = "ipq6018"

                if arch == "ipq5424":
                    flash = ipq5424_supported_flash

                if arch == "ipq5210":
                    flash = ipq5210_supported_flash

                if arch == "ipq9650":
                    flash = ipq9650_supported_flash

            elif option == "--fltype":
                flash = value
                for flash_type in flash.split(","):
                    if flash_type not in ["nor", "tiny-nor", "nand", "norplusnand", "emmc", "norplusemmc", "tiny-nor-debug", "norplusnand-gpt", "norplusemmc-gpt"]:
                        print("Invalid flash type: " + flash_type)
                        print_help()
                        return -1
            elif option == "--in":
                inDir = value
            elif option == "--dtc_path":
                dtcDir = value
            elif option == "--bootimg":
                bootImgDir = value
            elif option == "--tzimg":
                tzImgDir = value
            elif option == "--nhssimg":
                nhssImgDir = value
            elif option == "--rpmimg":
                rpmImgDir = value
            elif option == "--wififwimg":
                wififwImgDir = value
            elif option == "--gencdt":
                to_generate_cdt = "true"
            elif option == "--genxblcfg":
                to_generate_xblcfg = "true"
            elif option == "--genqccfg":
                to_generate_qccfg = "true"
            elif option == "--genmelf":
                to_generate_melf = "true"
            elif option == "--memory":
                memory = value
            elif option == "--flash_size":
                flash_size = value
            elif option == "--total_blocks":
                total_blocks = value
            elif option == "--genbootconf":
                to_generate_bootconf = "true"
            elif option == "--genbootconf_crc":
                to_generate_bootconf_crc = "true"
            elif option == "--genpart":
                to_generate_part = "true"
            elif option == "--genmbn":
                to_generate_mbn = "true"
            elif option == "--lk":
                to_generate_lk_mbn = "true"
            elif option == "--genbootldr":
                to_generate_bootldr = "true"
            elif option == "--genlicense":
                to_generate_license = "true"
            elif option == "--gentfambn":
                to_gen_tfa_mbn = "true"
            elif option == "--genopteembn":
                to_gen_optee_mbn = "true"
            elif option == "--soc":
                soc_dir = value

            elif (option == "-h" or option == "--help"):
                print_help()
                return 0

        srcDir="$$/scripts"
        srcDir = srcDir.replace('$$', cdir)
        configDir="$$/" + arch + "/config.xml"
        configDir = configDir.replace('$$', cdir)

        if inDir == "":
            inDir="$$/" + arch + "/in"
            inDir = inDir.replace('$$', cdir)

        inDir = os.path.abspath(inDir + "/")

        if not os.path.exists(inDir):
            os.makedirs(inDir)

        if dtcDir == "":
            dtcDir = inDir

        if bootImgDir != "":
            copy_images("BOOT", bootImgDir)
        if tzImgDir != "":
            copy_images("TZ", tzImgDir)
        if nhssImgDir != "":
            copy_images("NHSS" + mode, nhssImgDir)
        if rpmImgDir != "":
            copy_images("RPM", rpmImgDir)
        if wififwImgDir != "":
            copy_images("WIFIFW", wififwImgDir)

        if to_generate_cdt == "true":
            if gen_cdt() != 0:
                return -1

        if to_generate_xblcfg == "true":
            if gen_xblcfg() != 0:
                return -1

        if to_generate_qccfg == "true":
            if gen_qccfg() != 0:
                return -1

        if to_generate_bootconf == "true":
            if gen_bootconfig(0) != 0:
                return -1

        if to_generate_bootconf_crc == "true":
            if gen_bootconfig(1) != 0:
                return -1

        if to_generate_part == "true":
            if gen_part(flash) != 0:
                return -1

        if to_generate_bootldr == "true":
            if gen_bootldr() != 0:
                return -1

        if to_generate_license == "true":
            if arch == "ipq5424":
                if gen_license() != 0:
                    print("Failed to generate license bin")
                    return -1
            else:
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

                if gen_license() != 0:
                    print('Failed to generate license bin')
                    return -1

        if to_generate_mbn == "true":
            if arch == "ipq807x" or arch == "ipq6018" or arch == "ipq5018" or arch == "ipq9574" or arch == "ipq5332" or arch == "ipq5424" or arch == "ipq5210" or arch == "ipq9650":
                if arch == "ipq6018" or arch == "ipq9574" or arch == "ipq5332":
                    mbn_version = "6"
                elif arch == "ipq5424" or arch == "ipq5210" or arch == "ipq9650":
                    mbn_version = "7"
                if gen_mbn() != 0:
                    return -1
                if to_generate_lk_mbn == "true" and gen_lk_mbn() != 0:
                    return -1
            else:
                print("Invalid arch \"" + arch + "\" for mbn conversion")
                print("--genmbn is needed/used only for ipq807x, ipq6018, ipq5018, ipq9574, ipq5332, ipq5424, ipq5210 and ipq9650 type")

        if to_generate_melf == "true":
            if gen_melf() != 0:
                return -1

        if to_gen_tfa_mbn == "true" and gen_tfa_mbn() != 0:
            return -1

        if to_gen_optee_mbn == "true" and gen_optee_mbn() != 0:
            return -1

        # Clean up temp files after all operations are complete
        cleanup_intermediate_files()

        return 0
    else:
        print_help()
        return 0

if __name__ == '__main__':
    main()
