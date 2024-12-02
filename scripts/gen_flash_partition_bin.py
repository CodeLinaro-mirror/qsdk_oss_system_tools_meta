# ===========================================================================
# Copyright (c) 2024, Qualcomm Innovation Center, Inc. All rights reserved.
# SPDX-License-Identifier: ISC
# ===========================================================================

from collections import namedtuple

import xml.etree.ElementTree as ET
import os
import subprocess
import sys
from getopt import getopt
from getopt import GetoptError

cdir = os.path.dirname("")
cdir = os.path.abspath(cdir)
Nor_Params = namedtuple("Nor_Params", "pagesize pages_per_block total_blocks")
Nand_Params = namedtuple("nand_Params", "pagesize pages_per_block total_blocks")
emmc_layout = [ "user_", "boot0_", "boot1_", "rpmb_", "gpp1_", "gpp2_", "gpp3_", "gpp4_"]
outputdir = ""

def process_nand_device(pagesize, pages_per_block, total_blocks, entry, nand_type, nand_layout):

    global mbn_gen
    global nandsyspartition
    global partition_tool
    global cdir
    global ARCH_NAME
    global outputdir
    global QCN9000
    global QCN9224
    global flash_size

    nand_pagesize = pagesize
    nand_pages_per_block = pages_per_block
    nand_total_blocks = total_blocks

    if nand_layout != None:
        if nand_layout == "default":
            layout_name = ""
        else:
            layout_name = "-" + nand_layout

        if nand_type == "2k":
            nand_partition = "$$/" + ARCH_NAME + "/flash_partition/nand-partition"+ layout_name +".xml"
        else:
            nand_partition = "$$/" + ARCH_NAME + "/flash_partition/nand-"+ nand_type +"-partition"+ layout_name +".xml"
    elif nand_type == "audio-4k":
        nand_partition = "$$/" + ARCH_NAME + "/flash_partition/nand-audio-4k-partition.xml"
    elif nand_type == "audio-2k":
        nand_partition = "$$/" + ARCH_NAME + "/flash_partition/nand-audio-partition.xml"
    elif nand_type == "4k":
        if QCN9224:
            nand_partition = "$$/" + ARCH_NAME + "/flash_partition/nand-4k-partition-qcn9224.xml"
        else:
            nand_partition = "$$/" + ARCH_NAME + "/flash_partition/nand-4k-partition.xml"
    elif nand_type == "2k":
        if QCN9000:
            nand_partition = "$$/" + ARCH_NAME + "/flash_partition/nand-partition-qcn9000.xml"
        elif QCN9224:
            nand_partition = "$$/" + ARCH_NAME + "/flash_partition/nand-partition-qcn9224"+ flash_size +".xml"
        else:
            nand_partition = "$$/" + ARCH_NAME + "/flash_partition/nand-partition"+ flash_size +".xml"
    elif nand_type == "2k-256M":
        if QCN9000:
            nand_partition = "$$/" + ARCH_NAME + "/flash_partition/nand-partition-qcn9000"+ flash_size +".xml"
        elif QCN9224:
            nand_partition = "$$/" + ARCH_NAME + "/flash_partition/nand-partition-qcn9224"+ flash_size +".xml"
        else:
            nand_partition = "$$/" + ARCH_NAME + "/flash_partition/nand-partition"+ flash_size +".xml"

    nand_partition = nand_partition.replace('$$', cdir)

    nand_parts = Nand_Params(nand_pagesize, nand_pages_per_block, nand_total_blocks)

    mbn_gen = '$$/scripts/nand_mbn_generator.py'
    mbn_gen = mbn_gen.replace('$$', cdir)

    if ARCH_NAME == "ipq806x":
        partition_tool = outputdir + '/nor_tool'
    else:
        partition_tool = outputdir + '/partition_tool'
    os.chmod(partition_tool, 0o744)

    if nand_layout != None:
        if nand_type == "2k":
            nandsyspartition = outputdir + '/nand-system-partition-' + ARCH_NAME + layout_name + '.bin'
            nanduserpartition = 'nand-user-partition'+ layout_name +'.bin'
        else:
            nand_blocksize = int((nand_pagesize * nand_pages_per_block) / 1024)
            nandsyspartition = outputdir + '/nand-system-partition-' + ARCH_NAME + '-m' + str(nand_pagesize) + '-p' + str(nand_blocksize) + 'KiB' + layout_name + '.bin'
            nanduserpartition = 'nand-user-partition-m' + str(nand_pagesize) + '-p' + str(nand_blocksize) + 'KiB' + layout_name + '.bin'

    elif entry == False or (entry == True and nand_pagesize == 2048 and nand_type in ['2k', '2k-256M']):
        if QCN9000:
            nandsyspartition = outputdir + '/nand-system-partition-' + ARCH_NAME + '-qcn9000.bin'
            nanduserpartition = 'nand-user-partition-qcn9000.bin'
        elif QCN9224:
            nandsyspartition = outputdir + '/nand-system-partition-' + ARCH_NAME + '-qcn9224' + flash_size + '.bin'
            nanduserpartition = 'nand-user-partition-qcn9224'+ flash_size +'.bin'
        else:
            nandsyspartition = outputdir + '/nand-system-partition-' + ARCH_NAME + flash_size + '.bin'
            nanduserpartition = 'nand-user-partition'+ flash_size +'.bin'
    else:
        nand_blocksize = int((nand_pagesize * nand_pages_per_block) / 1024)
        if nand_type == "audio-2k" or nand_type == "audio-4k":
            nand_type = "audio-"
        elif nand_type  == "4k":
            nand_type = ""
        if QCN9224:
            nandsyspartition = outputdir + '/nand-' + nand_type + 'system-partition-' + ARCH_NAME + '-m' + str(nand_pagesize) + '-p' + str(nand_blocksize) + 'KiB-qcn9224.bin'
            nanduserpartition = 'nand-' + nand_type + 'user-partition-m' + str(nand_pagesize) + '-p' + str(nand_blocksize) + 'KiB-qcn9224.bin'
        else:
            nandsyspartition = outputdir + '/nand-' + nand_type + 'system-partition-' + ARCH_NAME + '-m' + str(nand_pagesize) + '-p' + str(nand_blocksize) + 'KiB.bin'
            nanduserpartition = 'nand-' + nand_type + 'user-partition-m' + str(nand_pagesize) + '-p' + str(nand_blocksize) + 'KiB.bin'

    nanduserbin= os.path.splitext(nanduserpartition)[0] + ".bin"

    print('\tNand page size: ' + str(nand_parts.pagesize) + ', pages/block: ' \
            + str(nand_parts.pages_per_block) + ', total blocks: ' \
            + str(nand_parts.total_blocks))
    print('\tPartition info: ' + nand_partition)

    print('\tCreating user partition')
    prc = subprocess.Popen(['python', mbn_gen, nand_partition,
                    nanduserbin], cwd=outputdir)
    prc.wait()
    if prc.returncode != 0:
        print('ERROR: unable to create user partition')
        return prc.returncode
    else:
        print('...User partition created')
    userpart_path = os.path.join(outputdir, nanduserbin)

    print('\tCreating system partition')
    prc = subprocess.Popen([
                    partition_tool,
                    '-s',
                    str(nand_parts.pagesize),
                    '-p',
                    str(nand_parts.pages_per_block),
                    '-b',
                    str(nand_parts.total_blocks),
                    '-u',
                    userpart_path,
                    '-o',
                    nandsyspartition,
                    ], cwd=outputdir)
    prc.wait()
    if prc.returncode != 0:
        print('ERROR: unable to create system partition')
        return prc.returncode
    else:
        print('...System partition created')
    return 0


def process_nand(config_path, flash_type):
    global mbn_gen
    global nandsyspartition
    global partition_tool
    global cdir
    global ARCH_NAME
    global outputdir
    global QCN9000
    global QCN9224
    global flash_size

    tree = ET.parse(config_path)
    root = tree.getroot()

    arch = root.find(".//data[@type='ARCH']/SOC")
    ARCH_NAME = str(arch.text)

    entry = False
    QCN9000 = False
    QCN9224 = False

    if ARCH_NAME == "ipq807x":
        QCN9000 = True

    if root.find(".//data[@type='NAND_PARAMETER']/entry") != None:
        entry = True
        entries = root.findall("./data[@type='NAND_PARAMETER']/entry")
        for nand_param in entries:
            nand_pagesize = int(nand_param.find(".//page_size").text)
            nand_pages_per_block = int(nand_param.find(".//pages_per_block").text)
            nand_total_blocks = int(nand_param.find(".//total_block").text)
            nand_type = nand_param.get('type')
            nand_layout = nand_param.get('layout')

            if flash_size == '-256M' and nand_type != '2k-256M':
                continue

            if flash_size != '-256M' and nand_type == '2k-256M':
                continue

            if ARCH_NAME == "ipq9574":
                QCN9224 = True

            if QCN9000:
                if process_nand_device(nand_pagesize, nand_pages_per_block, nand_total_blocks, entry, nand_type, None) != 0:
                    return -1
                QCN9000 = False
            elif QCN9224:
                if process_nand_device(nand_pagesize, nand_pages_per_block, nand_total_blocks, entry, nand_type, None) != 0:
                    return -1
                QCN9224 = False

            if process_nand_device(nand_pagesize, nand_pages_per_block, nand_total_blocks, True, nand_type, nand_layout) != 0:
                return -1
    else:
        nand_param = root.find(".//data[@type='NAND_PARAMETER']")
        nand_pagesize = int(nand_param.find('page_size').text)
        nand_pages_per_block = int(nand_param.find('pages_per_block').text)
        nand_total_blocks = int(nand_param.find('total_block').text)

        if ARCH_NAME == "ipq9574":
            QCN9224 = True

        if QCN9000:
            if process_nand_device(nand_pagesize, nand_pages_per_block, nand_total_blocks, entry, "2k", None) != 0:
                return -1
            QCN9000 = False
        elif QCN9224:
            if process_nand_device(nand_pagesize, nand_pages_per_block, nand_total_blocks, entry, "2k", None) != 0:
                return -1
            QCN9224 = False

        if process_nand_device(nand_pagesize, nand_pages_per_block, nand_total_blocks, entry, "2k", None) != 0:
            return -1

    return 0


def process_nor(config_path, flash_type):
    global mbn_gen
    global syspart
    global partition_tool
    global cdir
    global ARCH_NAME
    global outputdir

    tree = ET.parse(config_path)
    root = tree.getroot()

    arch = root.find(".//data[@type='ARCH']/SOC")
    ARCH_NAME = str(arch.text)

    mbn_gen = '$$/scripts/nand_mbn_generator.py'
    mbn_gen = mbn_gen.replace('$$', cdir)

    partition_tool = outputdir + '/partition_tool'
    os.chmod(partition_tool, 0o744)

    nor_param = None
    if flash_type == "tiny-nor" or flash_type == "tiny-nor-debug":
        nor_param = root.find(".//data[@type='TINY_NOR_PARAMETER']")

    if nor_param == None:
        nor_param = root.find(".//data[@type='NOR_PARAMETER']")

    if nor_param == None:
        if flash_type == "tiny-nor" or flash_type == "tiny-nor-debug":
            list_entry = ".//data[@type='TINY_NOR_PARAMETER']/entry"
        else:
            list_entry = ".//data[@type='NOR_PARAMETER']/entry"

        layout_entries = root.findall(list_entry)
        for nor_param in layout_entries:
            nor_pagesize = int(nor_param.find('page_size').text)
            nor_pages_per_block = int(nor_param.find('pages_per_block').text)
            nor_total_blocks = int(nor_param.find('total_block').text)
            block_size = (nor_pagesize * nor_pages_per_block) / 1024
            density = (block_size * nor_total_blocks) / 1024

            nor_partition = "$$/" + ARCH_NAME + "/flash_partition/" + flash_type + "-partition.xml"
            nor_partition = nor_partition.replace('$$', cdir)

            part_xml = ET.parse(nor_partition)
            part = part_xml.find(".//partitions/partition[name='0:MIBIB']")
            part[5].text = str(block_size)
            part[6].text = str(density)
            part_xml.write(nor_partition)

            nor_parts = Nor_Params(nor_pagesize, nor_pages_per_block, nor_total_blocks)

            syspart = outputdir + '/' + flash_type + '-system-partition-' + ARCH_NAME + '.bin'
            userpart = flash_type + '-user-partition.bin'
            noruserbin= os.path.splitext(userpart)[0] + ".bin"

            print('\tNor page size: ' + str(nor_parts.pagesize) + ', pages/block: ' \
                        + str(nor_parts.pages_per_block) + ', total blocks: ' \
                        + str(nor_parts.total_blocks) + ', partition info: ' + nor_partition)

            print('\tCreating user partition')
            prc = subprocess.Popen(['python', mbn_gen, nor_partition,
                                    noruserbin], cwd=outputdir)
            prc.wait()
            if prc.returncode != 0:
                print('ERROR: unable to create user partition')
                return prc.returncode
            else:
                print('...User partition created')

            userpart_path = os.path.join(outputdir, noruserbin)

            print('\tCreating system partition')
            prc = subprocess.Popen([
                            partition_tool,
                            '-s',
                            str(nor_parts.pagesize),
                            '-p',
                            str(nor_parts.pages_per_block),
                            '-b',
                            str(nor_parts.total_blocks),
                            '-c',
                            str(1),
                            '-u',
                            userpart_path,
                            '-o',
                            syspart,
                            ], cwd=outputdir)
            prc.wait()
            if prc.returncode != 0:
                print('ERROR: unable to create system partition')
                return prc.returncode
            else:
                print('...System partition created')

        return 0

    nor_pagesize = int(nor_param.find('page_size').text)
    nor_pages_per_block = int(nor_param.find('pages_per_block').text)
    nor_total_blocks = int(nor_param.find('total_block').text)
    block_size = (nor_pagesize * nor_pages_per_block) / 1024
    density = (block_size * nor_total_blocks) / 1024

    nor_partition = "$$/" + ARCH_NAME + "/flash_partition/" + flash_type + "-partition.xml"
    nor_partition = nor_partition.replace('$$', cdir)

    if ARCH_NAME != "ipq806x":
        root_part = ET.parse(nor_partition)
        part = root_part.find(".//partitions/partition[2]")
        part[5].text = str(block_size)
        part[6].text = str(density)
        root_part.write(nor_partition)

    nor_parts = Nor_Params(nor_pagesize, nor_pages_per_block, nor_total_blocks)

    syspart = outputdir + '/' + flash_type + '-system-partition-' + ARCH_NAME + '.bin'
    userpart = flash_type + '-user-partition.bin'
    noruserbin= os.path.splitext(userpart)[0] + ".bin"

    print('\tNor page size: ' + str(nor_parts.pagesize) + ', pages/block: ' \
            + str(nor_parts.pages_per_block) + ', total blocks: ' \
            + str(nor_parts.total_blocks) + ', partition info: ' + nor_partition)

    print('\tCreating user partition')
    prc = subprocess.Popen(['python', mbn_gen, nor_partition,
                        noruserbin], cwd=outputdir)
    prc.wait()
    if prc.returncode != 0:
        print('ERROR: unable to create user partition')
        return prc.returncode
    else:
        print('...User partition created')

    userpart_path = os.path.join(outputdir, noruserbin)

    print('\tCreating system partition')
    prc = subprocess.Popen([
                    partition_tool,
                    '-s',
                    str(nor_parts.pagesize),
                    '-p',
                    str(nor_parts.pages_per_block),
                    '-b',
                    str(nor_parts.total_blocks),
                    '-c',
                    str(1),
                    '-u',
                    userpart_path,
                    '-o',
                    syspart,
                    ], cwd=outputdir)
    prc.wait()
    if prc.returncode != 0:
        print('ERROR: unable to create system partition')
        return prc.returncode
    else:
        print('...System partition created')

    return 0


def process_norplusnand_device(nor_pagesize, nor_pages_per_block, nor_total_blocks,
                nand_pagesize, nand_pages_per_block, nand_total_blocks, entry, nand_layout):
    global mbn_gen
    global norplusnandsyspartition
    global partition_tool
    global cdir
    global ARCH_NAME
    global outputdir
    global QCN9000
    global QCN9224
    global flash_size

    nand_type = str(int(nand_pagesize / 1024)) + 'k'

    if nand_layout != None:
        if nand_layout == "default":
            layout_name = ""
        else:
            layout_name = "-" + nand_layout

        if nand_type == "2k":
            norplusnand_partition = "$$/" + ARCH_NAME + "/flash_partition/norplusnand-partition"+ layout_name +".xml"
        else:
            norplusnand_partition = "$$/" + ARCH_NAME + "/flash_partition/norplusnand-"+ nand_type +"-partition"+ layout_name +".xml"
    elif nand_pagesize == 2048:
        if QCN9000:
            norplusnand_partition = "$$/" + ARCH_NAME + "/flash_partition/norplusnand-partition-qcn9000.xml"
        elif QCN9224:
            norplusnand_partition = "$$/" + ARCH_NAME + "/flash_partition/norplusnand-partition-qcn9224"+ flash_size + ".xml"
        else:
            norplusnand_partition = "$$/" + ARCH_NAME + "/flash_partition/norplusnand-partition"+ flash_size +".xml"
    else:
        if QCN9224:
            norplusnand_partition = "$$/" + ARCH_NAME + "/flash_partition/norplusnand-4k-partition-qcn9224.xml"
        else:
            norplusnand_partition = "$$/" + ARCH_NAME + "/flash_partition/norplusnand-4k-partition.xml"

    norplusnand_partition = norplusnand_partition.replace('$$', cdir)

    if ARCH_NAME != "ipq806x":
        part_xml = ET.parse(norplusnand_partition)
        part = part_xml.find(".//partitions/partition[name='0:MIBIB']")
        block_size = (nor_pagesize * nor_pages_per_block) / 1024
        density = (block_size * nor_total_blocks) / 1024
        part[5].text = str(block_size)
        part[6].text = str(density)
        part_xml.write(norplusnand_partition)

    nand_parts = Nand_Params(nand_pagesize, nand_pages_per_block, nand_total_blocks)
    nor_parts = Nor_Params(nor_pagesize, nor_pages_per_block, nor_total_blocks)

    mbn_gen = '$$/scripts/nand_mbn_generator.py'
    mbn_gen = mbn_gen.replace('$$', cdir)

    if ARCH_NAME == "ipq806x":
        partition_tool = outputdir + '/nor_tool'
    else:
        partition_tool = outputdir + '/partition_tool'
    os.chmod(partition_tool, 0o744)

    if nand_layout != None:
        if nand_layout == "default":
            layout_name = ""
        else:
            layout_name = "-" + nand_layout

        if nand_type == "2k":
            norplusnandsyspartition = outputdir + '/norplusnand-system-partition-' + ARCH_NAME + layout_name + '.bin'
            userpart = 'norplusnand-user-partition'+ layout_name +'.bin'
        else:
            nand_blocksize = int((nand_pagesize * nand_pages_per_block) / 1024)
            norplusnandsyspartition = outputdir + '/norplusnand-system-partition-' + ARCH_NAME + '-m' + str(nand_pagesize) + '-p' + str(nand_blocksize) + 'KiB' + layout_name + '.bin'
            userpart = 'norplusnand-user-partition-m' + str(nand_pagesize) + '-p' + str(nand_blocksize) + 'KiB' + layout_name + '.bin'

    elif entry == False or (entry == True and nand_pagesize == 2048):
        if QCN9000:
            norplusnandsyspartition = outputdir + '/norplusnand-system-partition-' + ARCH_NAME + '-qcn9000.bin'
            userpart = 'norplusnand-user-partition-qcn9000.bin'
        elif QCN9224:
            norplusnandsyspartition = outputdir + '/norplusnand-system-partition-' + ARCH_NAME + '-qcn9224'+ flash_size +'.bin'
            userpart = 'norplusnand-user-partition-qcn9224.bin'
        else:
            norplusnandsyspartition = outputdir + '/norplusnand-system-partition-' + ARCH_NAME + flash_size +'.bin'
            userpart = 'norplusnand-user-partition'+ flash_size +'.bin'
    else:
        nand_blocksize = int((nand_pagesize * nand_pages_per_block) / 1024)
        if QCN9224:
            norplusnandsyspartition = outputdir + '/norplusnand-system-partition-' + ARCH_NAME + '-m' + str(nand_pagesize) + '-p' + str(nand_blocksize) + 'KiB-qcn9224.bin'
            userpart = 'norplusnand-user-partition-m' + str(nand_pagesize) + '-p' + str(nand_blocksize) + 'KiB-qcn9224.bin'
        else:
            norplusnandsyspartition = outputdir + '/norplusnand-system-partition-' + ARCH_NAME + '-m' + str(nand_pagesize) + '-p' + str(nand_blocksize) + 'KiB.bin'
            userpart = 'norplusnand-user-partition-m' + str(nand_pagesize) + '-p' + str(nand_blocksize) + 'KiB.bin'

    norplusnanduserbin= os.path.splitext(userpart)[0] +".bin"

    print('\tNor page size: ' + str(nor_parts.pagesize) + ', pages/block: ' \
            + str(nor_parts.pages_per_block) + ', total blocks: ' \
            + str(nor_parts.total_blocks))
    print('\tPartition info: ' + norplusnand_partition)

    print('\tCreating user partition')
    prc = subprocess.Popen(['python', mbn_gen, norplusnand_partition,
                            norplusnanduserbin], cwd=outputdir)
    prc.wait()
    if prc.returncode != 0:
        print('ERROR: unable to create user partition')
        return prc.returncode
    else:
        print('...User partition created')

    userpart_path = os.path.join(outputdir, norplusnanduserbin)

    print('\tCreating system partition')
    prc = subprocess.Popen([
                    partition_tool,
                    '-s',
                    str(nor_parts.pagesize),
                    '-p',
                    str(nor_parts.pages_per_block),
                    '-b',
                    str(nor_parts.total_blocks),
                    '-x',
                    str(nand_parts.pagesize),
                    '-y',
                    str(nand_parts.pages_per_block),
                    '-z',
                    str(nand_parts.total_blocks),
                    '-c',
                    str(1),
                    '-u',
                    userpart_path,
                    '-o',
                    norplusnandsyspartition,
                    ], cwd=outputdir)
    prc.wait()
    if prc.returncode != 0:
        print('ERROR: unable to create system partition')
        return prc.returncode
    else:
        print('...System partition created')
        return 0


def process_norplusnand(config_path, flash_type):
    global mbn_gen
    global norplusnandsyspartition
    global partition_tool
    global cdir
    global ARCH_NAME
    global outputdir
    global QCN9000
    global QCN9224
    global flash_size

    tree = ET.parse(config_path)
    root = tree.getroot()

    arch = root.find(".//data[@type='ARCH']/SOC")
    ARCH_NAME = str(arch.text)

    if root.find(".//data[@type='NORPLUSNAND_PARAMETER']/entry") != None:
        entries = root.findall("./data[@type='NORPLUSNAND_PARAMETER']/entry")
        for norplusnand_param in entries:
            nor_pagesize = int(norplusnand_param.find('page_size').text)
            nor_pages_per_block = int(norplusnand_param.find('pages_per_block').text)
            nor_total_blocks = int(norplusnand_param.find('total_block').text)

            nand_pagesize = int(norplusnand_param.find(".//nand_page_size").text)
            nand_pages_per_block = int(norplusnand_param.find(".//nand_pages_per_block").text)
            nand_total_blocks = int(norplusnand_param.find(".//nand_total_block").text)
            nand_layout = norplusnand_param.get('layout')

            if process_norplusnand_device(nor_pagesize,
                    nor_pages_per_block, nor_total_blocks, nand_pagesize,
                    nand_pages_per_block, nand_total_blocks, True, nand_layout) != 0:
                return -1

        return 0

    entry = False
    QCN9000 = False
    QCN9224 = False

    nor_param = root.find(".//data[@type='NOR_PARAMETER']")
    nor_pagesize = int(nor_param.find('page_size').text)
    nor_pages_per_block = int(nor_param.find('pages_per_block').text)
    nor_total_blocks = int(nor_param.find('total_block').text)

    if ARCH_NAME == "ipq807x":
        QCN9000 = True

    if root.find(".//data[@type='NAND_PARAMETER']/entry") != None:
        entry = True
        entries = root.findall("./data[@type='NAND_PARAMETER']/entry")

        for nand_param in entries:
            nand_pagesize = int(nand_param.find(".//page_size").text)
            nand_pages_per_block = int(nand_param.find(".//pages_per_block").text)
            nand_total_blocks = int(nand_param.find(".//total_block").text)
            nand_type = nand_param.get('type')

            if flash_size == '-256M' and nand_type != '2k-256M':
                continue

            if flash_size != '-256M' and nand_type == '2k-256M':
                continue

            if ARCH_NAME == "ipq9574":
                QCN9224 = True

            if QCN9000:
                if process_norplusnand_device(nor_pagesize,
                        nor_pages_per_block, nor_total_blocks, nand_pagesize,
                        nand_pages_per_block, nand_total_blocks, entry, None) != 0:
                    return -1
                QCN9000 = False
            elif QCN9224:
                if process_norplusnand_device(nor_pagesize,
                        nor_pages_per_block, nor_total_blocks, nand_pagesize,
                        nand_pages_per_block, nand_total_blocks, entry, None) != 0:
                    return -1
                QCN9224 = False

            if process_norplusnand_device(nor_pagesize,
                    nor_pages_per_block, nor_total_blocks, nand_pagesize,
                    nand_pages_per_block, nand_total_blocks, entry, None) != 0:
                return -1
    else:
        nand_param = root.find(".//data[@type='NAND_PARAMETER']")
        nand_pagesize = int(nand_param.find('page_size').text)
        nand_pages_per_block = int(nand_param.find('pages_per_block').text)
        nand_total_blocks = int(nand_param.find('total_block').text)

        if ARCH_NAME == "ipq9574":
            QCN9224 = True

        if QCN9000:
            if process_norplusnand_device(nor_pagesize,
                        nor_pages_per_block, nor_total_blocks, nand_pagesize,
                        nand_pages_per_block, nand_total_blocks, entry) != 0:
                return -1
            QCN9000 = False
        elif QCN9224:
            if process_norplusnand_device(nor_pagesize,
                        nor_pages_per_block, nor_total_blocks, nand_pagesize,
                        nand_pages_per_block, nand_total_blocks, entry) != 0:
                return -1
            QCN9224 = False

        if process_norplusnand_device(nor_pagesize,
                        nor_pages_per_block, nor_total_blocks, nand_pagesize,
                        nand_pages_per_block, nand_total_blocks, entry) != 0:
                return -1

    return 0

def process_nor_gpt(config_path, flash_type):
    global ptool
    global msp
    global ARCH_NAME
    global outputdir
    global total_blocks

    tree = ET.parse(config_path)
    root = tree.getroot()

    arch = root.find(".//data[@type='ARCH']/SOC")
    ARCH_NAME = str(arch.text)

    ptool = '$$/scripts/ptool.py'
    ptool = ptool.replace('$$', cdir)

    msp = '$$/scripts/msp.py'
    msp = msp.replace('$$', cdir)

    partition = "$$/" + ARCH_NAME + "/flash_partition/nor-gpt-partition.xml"
    partition = partition.replace('$$', cdir)

    if flash_type == "norplusnand-gpt":
        list_entry = ".//data[@type='NORPLUSNAND-GPT_PARAMETER']/entry"
    elif flash_type == "norplusemmc-gpt":
        list_entry = ".//data[@type='NORPLUSEMMC-GPT_PARAMETER']/entry"

    if root.find(list_entry) != None:
        entries = root.findall(list_entry)
        for layout_entry in entries:
            for nor_gpt_param in layout_entry:
                nor_total_blocks = nor_gpt_param.find(".//total_block").text
                nor_gpt_outname = nor_gpt_param.find(".//partition_mbn").text
                nor_gpt_bkp_outname = nor_gpt_param.find(".//partition_mbn_backup").text
                nor_gpt_layout = nor_gpt_param.get('layout')
                physical_partition = nor_gpt_param.get('physical_partition')

                rawprogram_fname = "nor_rawprogram" + physical_partition + ".xml"
                patch_fname = "nor_patch" + physical_partition + ".xml"
                gpt_fname = "nor_gpt_main" + physical_partition + ".bin"
                gpt_bkp_fname = "nor_gpt_backup" + physical_partition + ".bin"

                print('\tTotal blocks: ' + nor_total_blocks)
                print('\tPartition info: ' + partition)
                print('\tPath: ' + outputdir)

                print('\tCreating ' + rawprogram_fname + ' and ' + patch_fname)
                prc = subprocess.Popen(['python', ptool, '-x', partition, '-p', physical_partition, '-d', nor_total_blocks], cwd=outputdir)
                prc.wait()
                if prc.returncode != 0:
                    print('ERROR: unable to create rawprogram0.xml and patch0.xml')
                    return prc.returncode

                print('...'+ rawprogram_fname +' and '+ patch_fname +' created')
                rawprogram_path = os.path.join(outputdir, rawprogram_fname)
                patch_path = os.path.join(outputdir, patch_fname)

                print('\t rawprogram' + rawprogram_path)
                print('\t patch' + patch_path)

                print('\tRunning msp.py to update '+ gpt_fname + ' partition')

                prc = subprocess.Popen([
                        'python',
                        msp,
                        '-b',
                        str(4096),
                        '-r',
                        rawprogram_path,
                        '-p',
                        patch_path,
                        '-d',
                        nor_total_blocks,
                        '-n',
                    ], cwd=outputdir)
                prc.wait()

                if prc.returncode != 0:
                    print('ERROR: unable to create system partition')
                    return prc.returncode
                else:
                    print('...System partition created')

                if gpt_fname != nor_gpt_outname:
                    print('\tCopying ' + gpt_fname + ' as ' + nor_gpt_outname)
                    prc = subprocess.Popen(['cp', gpt_fname, nor_gpt_outname], cwd=outputdir)
                    prc.wait()
                    if prc.returncode != 0:
                        print('ERROR: unable to create rawprogram0.xml and patch0.xml')
                        return prc.returncode

                if gpt_bkp_fname != nor_gpt_bkp_outname:
                   print('\tCopying ' + gpt_bkp_fname + ' as ' + nor_gpt_bkp_outname)
                   prc = subprocess.Popen(['cp', gpt_bkp_fname, nor_gpt_bkp_outname], cwd=outputdir)
                   prc.wait()
                   if prc.returncode != 0:
                       print('ERROR: unable to create rawprogram0.xml and patch0.xml')
                       return prc.returncode

    return 0

def process_emmc(config_path, flash_type):
    global ptool
    global msp
    global ARCH_NAME
    global outputdir

    tree = ET.parse(config_path)
    root = tree.getroot()

    arch = root.find(".//data[@type='ARCH']/SOC")
    ARCH_NAME = str(arch.text)

    ptool = '$$/scripts/ptool.py'
    ptool = ptool.replace('$$', cdir)

    msp = '$$/scripts/msp.py'
    msp = msp.replace('$$', cdir)

    list_entry = ".//data[@type='EMMC_PARAMETER']/entry"
    if root.find(list_entry) != None:
        entries = root.findall(list_entry)
        for layout_entry in entries:
            gpt_layout = layout_entry.get('layout')
            layout_name = ""
            gpt_prefix = "emmc"

            if gpt_layout != None:
                if gpt_layout != "default":
                    layout_name = "-" + gpt_layout
                    gpt_prefix = "emmc_" + gpt_layout


            emmc_partition = "$$/" + ARCH_NAME + "/flash_partition/emmc-partition" + layout_name + ".xml"
            emmc_partition = emmc_partition.replace('$$', cdir)

            for gpt_param in layout_entry:
                total_blocks = gpt_param.find(".//total_block").text
                gpt_outname = gpt_param.find(".//partition_mbn").text
                gpt_bkp_outname = gpt_param.find(".//partition_mbn_backup").text
                physical_partition = gpt_param.get('physical_partition')

                gpt_out_prefix = gpt_prefix + "_" + emmc_layout[int(physical_partition)]
                rawprogram_fname = gpt_out_prefix + "rawprogram" + physical_partition + ".xml"
                patch_fname = gpt_out_prefix + "patch" + physical_partition + ".xml"
                gpt_fname = gpt_out_prefix + "gpt_main" + physical_partition + ".bin"
                gpt_bkp_fname = gpt_out_prefix + "gpt_backup" + physical_partition + ".bin"

                print('\tTotal blocks: ' + total_blocks)
                print('\tPartition info: ' + emmc_partition)
                print('\tPath: ' + outputdir)

                print('\tCreating ' + rawprogram_fname + ' and ' + patch_fname)

                prc = subprocess.Popen(['python', ptool, '-x', emmc_partition, '-p', physical_partition, '-d', total_blocks, '-l', gpt_out_prefix], cwd=outputdir)
                prc.wait()
                if prc.returncode != 0:
                    print('ERROR: unable to create rawprogram0.xml and patch0.xml')
                    return prc.returncode

                print('...'+ rawprogram_fname +' and '+ patch_fname +' created')
                rawprogram_path = os.path.join(outputdir, rawprogram_fname)
                patch_path = os.path.join(outputdir, patch_fname)

                print('\t rawprogram' + rawprogram_path)
                print('\t patch' + patch_path)

                print('\tRunning msp.py to update '+ gpt_fname + ' partition')

                prc = subprocess.Popen([
                        'python',
                        msp,
                        '-r',
                        rawprogram_path,
                        '-p',
                        patch_path,
                        '-d',
                        total_blocks,
                        '-n',
                    ], cwd=outputdir)
                prc.wait()

                if prc.returncode != 0:
                    print('ERROR: unable to create system partition')
                    return prc.returncode
                else:
                    print('...System partition created')

                if gpt_fname != gpt_outname:
                    print('\tCopying ' + gpt_fname + ' as ' + gpt_outname)
                    prc = subprocess.Popen(['cp', gpt_fname, gpt_outname], cwd=outputdir)
                    prc.wait()
                    if prc.returncode != 0:
                        print('ERROR: unable to create rawprogram0.xml and patch0.xml')
                        return prc.returncode

                if gpt_bkp_fname != gpt_bkp_outname:
                    print('\tCopying ' + gpt_bkp_fname + ' as ' + gpt_bkp_outname)
                    prc = subprocess.Popen(['cp', gpt_bkp_fname, gpt_bkp_outname], cwd=outputdir)
                    prc.wait()
                    if prc.returncode != 0:
                        print('ERROR: unable to create rawprogram0.xml and patch0.xml')
                        return prc.returncode

        return 0

    emmc_partition = "$$/" + ARCH_NAME + "/flash_partition/emmc-partition.xml"
    emmc_partition = emmc_partition.replace('$$', cdir)

    emmc_total_blocks = None
    emmc_entry = root.find(".//data[@type='EMMC_PARAMETER']/total_block")
    total_blocks = int(emmc_entry.text)
    emmc_total_blocks = total_blocks

    print('\tTotal blocks: ' + str(emmc_total_blocks))
    print('\tPartition info: ' + emmc_partition)
    print('\temmc path: ' + outputdir)

    print('\tCreating rawprogram0.xml and patch0.xml')
    prc = subprocess.Popen(['python', ptool, '-x', emmc_partition], cwd=outputdir)
    prc.wait()
    if prc.returncode != 0:
        print('ERROR: unable to create rawprogram0.xml and patch0.xml')
        return prc.returncode
    else:
        print('...rawprogram0.xml and patch0.xml created')

    rawprogram_path = os.path.join(outputdir, 'rawprogram0.xml')
    patch_path = os.path.join(outputdir, 'patch0.xml')

    print('\t rawprogram' + rawprogram_path)
    print('\t patch' + patch_path)

    print('\tRunning msp.py to update gpt_main0.bin partition')
    prc = subprocess.Popen([
            'python',
            msp,
            '-r',
            rawprogram_path,
            '-p',
            patch_path,
            '-d',
            str(emmc_total_blocks),
            '-n',
        ], cwd=outputdir)
    prc.wait()

    if prc.returncode != 0:
        print('ERROR: unable to create system partition')
        return prc.returncode
    else:
        print('...System partition created')

    if ARCH_NAME == "ipq9574":

        print("\n------------------------------------------------------------------------------\n")
        print('Start creating System partition for qcn9224\n')

        print('\tCreating rawprogram2.xml and patch2.xml')
        prc = subprocess.Popen(['python', ptool, '-x', emmc_partition, '-p', '2'], cwd=outputdir)
        prc.wait()
        if prc.returncode != 0:
            print('ERROR: unable to create rawprogram2.xml and patch2.xml')
            return prc.returncode
        else:
            print('...rawprogram2.xml and patch2.xml created')

        rawprogram_path = os.path.join(outputdir, 'rawprogram2.xml')
        patch_path = os.path.join(outputdir, 'patch2.xml')

        print('\t rawprogram' + rawprogram_path)
        print('\t patch' + patch_path)

        print('\tRunning msp.py to update gpt_main2.bin partition')
        prc = subprocess.Popen([
                'python',
                msp,
                '-r',
                rawprogram_path,
                '-p',
                patch_path,
                '-d',
                str(emmc_total_blocks),
                '-n',
                ], cwd=outputdir)
        prc.wait()

        if prc.returncode != 0:
            print('ERROR: unable to create system partition')
            return prc.returncode
        else:
            print('...System partition created')

    return 0


def process_norplusemmc_device(nor_pagesize, nor_pages_per_block, nor_total_blocks, nor_layout):
    global mbn_gen
    global syspart
    global partition_tool
    global cdir
    global ARCH_NAME
    global outputdir
    global QCN9224

    if nor_layout != None:
        if nor_layout == "default":
            layout_name = ""
        else:
            layout_name = "-" + nand_layout

        norplusemmc_partition = "$$/" + ARCH_NAME + "/flash_partition/norplusemmc-partition" + layout_name + ".xml"
        syspart = outputdir + '/norplusemmc-system-partition-' + ARCH_NAME + layout_name + '.bin'
        userpart = 'norplusemmc-user-partition' + layout_name + '.bin'
    elif QCN9224:
        norplusemmc_partition = "$$/" + ARCH_NAME + "/flash_partition/norplusemmc-partition-qcn9224.xml"
        syspart = outputdir + '/norplusemmc-system-partition-' + ARCH_NAME + '-qcn9224.bin'
        userpart = 'norplusemmc-user-partition-qcn9224.bin'
    else:
        norplusemmc_partition = "$$/" + ARCH_NAME + "/flash_partition/norplusemmc-partition.xml"
        syspart = outputdir + '/norplusemmc-system-partition-' + ARCH_NAME + '.bin'
        userpart = 'norplusemmc-user-partition.bin'

    norplusemmc_partition = norplusemmc_partition.replace('$$', cdir)

    if ARCH_NAME != "ipq806x":
        root_part = ET.parse(norplusemmc_partition)
        part = root_part.find(".//partitions/partition[2]")
        block_size = (nor_pagesize * nor_pages_per_block) / 1024
        density = (block_size * nor_total_blocks) / 1024
        part[5].text = str(block_size)
        part[6].text = str(density)
        root_part.write(norplusemmc_partition)

    nor_parts = Nor_Params(nor_pagesize, nor_pages_per_block, nor_total_blocks)

    mbn_gen = '$$/scripts/nand_mbn_generator.py'
    mbn_gen = mbn_gen.replace('$$', cdir)

    if ARCH_NAME == "ipq806x":
        partition_tool = outputdir + '/nor_tool'
    else:
        partition_tool = outputdir + '/partition_tool'
    os.chmod(partition_tool, 0o744)

    norplusemmcuserbin= os.path.splitext(userpart)[0] + ".bin"

    print('\tNor page size: ' + str(nor_parts.pagesize) + ', pages/block: ' \
            + str(nor_parts.pages_per_block) + ', total blocks: ' \
            + str(nor_parts.total_blocks) + ', partition info: ' + norplusemmc_partition)

    print('\tCreating user partition')
    prc = subprocess.Popen(['python', mbn_gen, norplusemmc_partition,
                            norplusemmcuserbin], cwd=outputdir)
    prc.wait()
    if prc.returncode != 0:
        print('ERROR: unable to create user partition')
        return prc.returncode
    else:
        print('...User partition created')

    userpart_path = os.path.join(outputdir, norplusemmcuserbin)

    print('\tCreating system partition')
    prc = subprocess.Popen([
                    partition_tool,
                    '-s',
                    str(nor_parts.pagesize),
                    '-p',
                    str(nor_parts.pages_per_block),
                    '-b',
                    str(nor_parts.total_blocks),
                    '-c',
                    str(1),
                    '-u',
                    userpart_path,
                    '-o',
                    syspart,
                    ], cwd=outputdir)
    prc.wait()
    if prc.returncode != 0:
        print('ERROR: unable to create system partition')
        return prc.returncode
    else:
        print('...System partition created')

    return 0


def process_norplusemmc(config_path, flash_type):
    global mbn_gen
    global syspart
    global partition_tool
    global cdir
    global ptool
    global msp
    global ARCH_NAME
    global outputdir
    global QCN9224

    tree = ET.parse(config_path)
    root = tree.getroot()

    arch = root.find(".//data[@type='ARCH']/SOC")
    ARCH_NAME = str(arch.text)

    ptool = '$$/scripts/ptool.py'
    ptool = ptool.replace('$$', cdir)

    msp = '$$/scripts/msp.py'
    msp = msp.replace('$$', cdir)

    emmc_partition = "$$/" + ARCH_NAME + "/flash_partition/emmc-partition.xml"
    emmc_partition = emmc_partition.replace('$$', cdir)

    list_entry = ".//data[@type='NORPLUSEMMC_PARAMETER']/entry"
    if root.find(list_entry) != None:
        emmc_partition = "$$/" + ARCH_NAME + "/flash_partition/sec-emmc-partition.xml"
        emmc_partition = emmc_partition.replace('$$', cdir)

        entries = root.findall(list_entry)

        for layout_entry in entries:
            layout = layout_entry.get('layout')

            for norplusemmc_param in layout_entry:
                physical_partition = norplusemmc_param.get('physical_partition')

                nor_pagesize = int(norplusemmc_param.find('page_size').text)
                nor_pages_per_block = int(norplusemmc_param.find('pages_per_block').text)
                nor_total_blocks = int(norplusemmc_param.find('total_block').text)

                emmc_total_blocks = int(norplusemmc_param.find('emmc_total_block').text)
                gpt_outname = norplusemmc_param.find(".//partition_mbn").text
                gpt_bkp_outname = norplusemmc_param.find(".//partition_mbn_backup").text

                if process_norplusemmc_device(nor_pagesize, nor_pages_per_block, nor_total_blocks, layout) != 0:
                    return -1

                rawprogram_fname = "rawprogram" + physical_partition + ".xml"
                patch_fname = "patch" + physical_partition + ".xml"
                gpt_fname = "gpt_main" + physical_partition + ".bin"
                gpt_bkp_fname = "gpt_backup" + physical_partition + ".bin"

                print('\tTotal blocks: ' + str(emmc_total_blocks))
                print('\tPartition info: ' + emmc_partition)
                print('\tPath: ' + outputdir)

                print('\tCreating ' + rawprogram_fname + ' and ' + patch_fname)
                prc = subprocess.Popen(['python', ptool, '-x', emmc_partition, '-p', physical_partition], cwd=outputdir)
                prc.wait()
                if prc.returncode != 0:
                    print('ERROR: unable to create rawprogram0.xml and patch0.xml')
                    return prc.returncode

                print('...'+ rawprogram_fname +' and '+ patch_fname +' created')
                rawprogram_path = os.path.join(outputdir, rawprogram_fname)
                patch_path = os.path.join(outputdir, patch_fname)

                print('\t rawprogram' + rawprogram_path)
                print('\t patch' + patch_path)

                print('\tRunning msp.py to update '+ gpt_fname + ' partition')

                prc = subprocess.Popen([
                        'python',
                        msp,
                        '-r',
                        rawprogram_path,
                        '-p',
                        patch_path,
                        '-d',
                        str(emmc_total_blocks),
                        '-n',
                    ], cwd=outputdir)
                prc.wait()

                if prc.returncode != 0:
                    print('ERROR: unable to create system partition')
                    return prc.returncode
                else:
                    print('...System partition created')

                if gpt_fname != gpt_outname:
                    print('\tCopying ' + gpt_fname + ' as ' + gpt_outname)
                    prc = subprocess.Popen(['cp', gpt_fname, gpt_outname], cwd=outputdir)
                    prc.wait()
                    if prc.returncode != 0:
                        print('ERROR: unable to create rawprogram0.xml and patch0.xml')
                        return prc.returncode

                if gpt_bkp_fname != gpt_bkp_outname:
                    print('\tCopying ' + gpt_bkp_fname + ' as ' + gpt_bkp_outname)
                    prc = subprocess.Popen(['cp', gpt_bkp_fname, gpt_bkp_outname], cwd=outputdir)
                    prc.wait()
                    if prc.returncode != 0:
                        print('ERROR: unable to create rawprogram0.xml and patch0.xml')
                        return prc.returncode

            return 0

    QCN9224 = False

    if ARCH_NAME == "ipq9574":
        QCN9224 = True

    blocks = root.find(".//data[@type='EMMC_PARAMETER']")
    emmc_total_blocks = int(blocks.find('total_block').text)

    nor_param = root.find(".//data[@type='NORPLUSEMMC_PARAMETER']")
    nor_pagesize = int(nor_param.find('page_size').text)
    nor_pages_per_block = int(nor_param.find('pages_per_block').text)
    nor_total_blocks = int(nor_param.find('total_block').text)

    if QCN9224:
        if process_norplusemmc_device(nor_pagesize, nor_pages_per_block, nor_total_blocks, None) != 0:
            return -1
        QCN9224 = False

    if process_norplusemmc_device(nor_pagesize, nor_pages_per_block, nor_total_blocks, None) != 0:
        return -1

    print('\tCreating rawprogram1.xml and patch1.xml')
    prc = subprocess.Popen(['python', ptool, '-x', emmc_partition, '-p', '1'], cwd=outputdir)
    prc.wait()
    if prc.returncode != 0:
        print('ERROR: unable to create rawprogram1.xml and patch1.xml')
        return prc.returncode
    else:
        print('...rawprogram1.xml and patch1.xml created')

    rawprogram_path = os.path.join(outputdir, 'rawprogram1.xml')
    patch_path = os.path.join(outputdir, 'patch1.xml')

    print('\t rawprogram' + rawprogram_path)
    print('\t patch' + patch_path)

    print('\tRunning msp.py to update gpt_main0.bin partition')
    prc = subprocess.Popen([
            'python',
            msp,
            '-r',
            rawprogram_path,
            '-p',
            patch_path,
            '-d',
            str(emmc_total_blocks),
            '-n',
            ], cwd=outputdir)
    prc.wait()
    if prc.returncode != 0:
        print('ERROR: unable to create system partition')
        return prc.returncode
    else:
        print('...System partition created')

    if ARCH_NAME == "ipq9574":
        print("\n------------------------------------------------------------------------------\n")
        print('Start creating System partition for qcn9224\n')

        print('\tCreating rawprogram3.xml and patch3.xml')
        prc = subprocess.Popen(['python', ptool, '-x', emmc_partition, '-p', '3'], cwd=outputdir)
        prc.wait()
        if prc.returncode != 0:
            print('ERROR: unable to create rawprogram3.xml and patch3.xml')
            return prc.returncode
        else:
            print('...rawprogram3.xml and patch3.xml created')

        rawprogram_path = os.path.join(outputdir, 'rawprogram3.xml')
        patch_path = os.path.join(outputdir, 'patch3.xml')

        print('\t rawprogram' + rawprogram_path)
        print('\t patch' + patch_path)

        print('\tRunning msp.py to update gpt_main2.bin partition')
        prc = subprocess.Popen([
                'python',
                msp,
                '-r',
                rawprogram_path,
                '-p',
                patch_path,
                '-d',
                str(emmc_total_blocks),
                '-n',
                ], cwd=outputdir)
        prc.wait()

        if prc.returncode != 0:
            print('ERROR: unable to create system partition')
            return prc.returncode
        else:
            print('...System partition created')

    return 0


def main():

    global cdir
    global ARCH_NAME
    global outputdir
    global flash_size
    global total_blocks
    flash_size = ""

    funcdict = {
            'nor': process_nor,
            'tiny-nor': process_nor,
            'nand': process_nand,
            'norplusnand': process_norplusnand,
            'norplusnand-gpt': process_nor_gpt,
            'norplusemmc-gpt': process_nor_gpt,
            'emmc': process_emmc,
            'norplusemmc': process_norplusemmc,
            'tiny-nor-debug': process_nor
    }

    if len(sys.argv) > 1:
        try:
            opts, args = getopt(sys.argv[1:], "c:f:o:s:t:")
        except GetoptError as e:
            print("Configuration xml, flash type and output path are needed to generate cdt files")
            raise

        for option, value in opts:
            if option == "-c":
                config_path = value
            if option == "-o":
                outputdir = value
            if option == "-f":
                flash_type = value
                print(flash_type)
            if option == "-t":
                total_blocks = value
            if option == "-s":
                if value != "":
                    flash_size = "-" + value
    else:
        print("Configuration xml, flash type and output path are needed to generate cdt files")

    if funcdict[flash_type](config_path, flash_type) < 0:
        return -1

if __name__ == '__main__':
    main()
