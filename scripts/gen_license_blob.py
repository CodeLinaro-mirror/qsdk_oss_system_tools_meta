#!/usr/bin/python
# ===========================================================================
# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: ISC
# ===========================================================================


import os
import sys
import struct
import argparse
import fnmatch
import hashlib
import base64
import binascii
import subprocess

'''
License Partition Format
--------------------------------------------------------------------------------------------------
|   DataStore Hdr0    |   Meta1....N   |  License1...N  |    DataStore Ftr0     |                |
|-------------------------------------------------------------------------------|                |
|Signature, Version,  |identifier_len, |   pfm files    | same as DataStoreHdr0 |                |
|Age, WriteMethod,    |identifier      |                |                       |     COPY 2     |
|cfgDataSize,         |                |                |                       |                |
|MaxPayloadDectors,   |                |                |                       |   (repeated)   |
|ActivePayloadSectors,|                |                |                       |                |
|SyncCount, CRC       |                |                |                       |                |
--------------------------------------------------------------------------------------------------
'''

# Name & version of the tool
QLS_TOOL_NAME = 'qlstool'
QLS_TOOL_VERSION = '2.0'

__version__ = QLS_TOOL_NAME + ' ' + QLS_TOOL_VERSION

# Path definitions
DEFAULT_QLS_DIR_PATH = os.getcwd()

# Tool configuration
DEFAULT_FILE_NAME = 'qweslicstore'
PFM_FILE_MAXSIZE = 10240

COPY_1 = 1
COPY_2 = 2

ptbl_copy1 = {}
ptbl_copy2 = {}

partition_size = 0
store_size = 0
slots_per_store = 0
max_licenses = 0

data_store_hdr = 0
data_store_ftr = 0

MAX_SERIAL_NUMBER_SIZE = 21
TOC_INDEX = 1

IDENTIFIER_LEN = 4
IDENTIFIER_SIZE = 8
ATTACH_LEN = 1
ATTACH_NUM = 1
RESERVED = 6
TOC_ENTRY_IDENTIFIER_SIZE = IDENTIFIER_LEN + IDENTIFIER_SIZE + ATTACH_LEN + ATTACH_NUM + RESERVED

NO_OF_COPIES = 2
SLOT_SIZE = 4096

DATA_MGR_HDR = 1
META_HDR = 1
DATA_MGR_FTR = 1

CRC32_SEED = 0xffffffff

EMMC_MIN_PART_SIZE = 128 #size in KB
# For emmc erase size could be as low as 512 bytes
EMMC_ERASE_SIZE = 512
# For other flash types erase size is in KB
NOR_ERASE_SIZE = 64
NAND2K_ERASE_SIZE = 128
NAND4K_ERASE_SIZE = 256

DATA_STORE_MGR_SIGNATURE = 0x72745344
DATA_STORE_LATEST_VERSION = 0x0103
WRITE_METHOD_SIMPLE_PING_PONG_TYPE = 1
MAX_AGE_VALUE = 4

MAX_META = SLOT_SIZE / TOC_ENTRY_IDENTIFIER_SIZE

SOC = 0
ATTACH1 = 1
ATTACH2 = 2
ATTACH3 = 3
ATTACH4 = 4
ATTACH5 = 5

staging_dir = r'/tmp/lic_tmp/'

def getOffset(slot, copy):
    """Returns an offset for the corresponding given slot and copy."""
    if copy == COPY_1:
        for key, value in ptbl_copy1.items():
            if slot == key:
                return value
            else:
                continue

    elif copy == COPY_2:
        for key, value in ptbl_copy2.items():
            if slot == key:
                return value
            else:
                continue

    else:
        return

def createEmptyPartition(path, size):
    """Creates an empty partition."""
    qls = open(path, "w+b")
    bytes = [0] * (size)
    qls.write(struct.pack('%iB' % (size), *bytes))
    qls.close()

def updatePartition(path, offset, data):
    """Updates the partition with the given data and at the given offset."""
    qls = open(path, "r+b")
    qls.seek(offset)
    qls.write(data)
    qls.close()

def filterUniqueFiles(files):
    """Skip the duplicate pfm files and returns the dict that contains unique pfmfliles list"""
    pfm_unique = {}
    for fname in files:
        file_hash = hashlib.md5(open(fname, 'rb').read()).hexdigest()
        if file_hash not in pfm_unique:
            pfm_unique[file_hash] = fname
        else:
            print('Skipping "%s" as it is a duplicate of "%s"' % (fname, pfm_unique[file_hash]))
    return pfm_unique.values()

def readPFM(filename):
    pem = ""
    in_cert = False

    with open(filename, "r")as f:
        for l in f.readlines():
            if in_cert:
                if 0 == l.find("-----END CERTIFICATE-----"):
                    break
                else:
                    pem += l
            else:
                if 0 == l.find("-----BEGIN CERTIFICATE-----"):
                    in_cert = True

    return bytearray(base64.b64decode(pem))

TAG_MASK = 0x1f
def readDERIdent(der):
    # for now, just return tag
    #print("ident byte = 0x%x" % (der[0]))
    return (der[0] & TAG_MASK, der[1:])

def readUnsignedBytes(der, length):
    if length < 1 or length > 4:
        raise Exception("Unexpected length %d bytes" % (length))
    val = 0
    for i in range(length):
        val = (val << 8) | der[i]
    return (val, der[length:])

def readDERLen(der):
    length_byte = der[0]
    if length_byte == 0xff or length_byte == 0x80:
        raise Exception("Invalid or indefinite length")
    if length_byte < 0x80:
        return (length_byte, der[1:])
    return(readUnsignedBytes(der[1:], length_byte & 0x7f))

def readDERItem(der):
    (ident, der) = readDERIdent(der)
    (length, der) = readDERLen(der)
    return (ident, der[0:length], der[length:])

# From section 8.3.2:
# If ... an integer value encoding consit[s] of more than one octet, then:
# the bits of the first octet and bit 8 of the second octed:
#   a) shall not be all ones
#   b) shall not be all zeroes
#
# These rules ensure that an integer value is always incoded in the smallest
# possible number of octets.
#
# The upshot of this is that -1 will always be encoded with length 1 (02 01 FF),
# while -129 will be encoded with length 2 as (02 02 FF 7F),
# And e.g. 65535 will be encoded with length 3.  (02 03 00 FF FF)

def readLargePositiveInteger(der):
    (ident, octets, remainder) = readDERItem(der)
    if ident != 2:
        raise Exception("ident %d when 2 was expected" % (ident))
    if len(octets) >= 1:
        if octets[0] & 0x80 == 0x80:
            raise Exception("Unexpected negative integer")
        if octets[0] == 0:
            # trim leading octet
            return (octets[1:], remainder)
    return (octets, remainder)

def find_akid(der_bytes):
    akid_oid_bytes = bytearray([0x55, 0x1d, 0x23])
    akid_oid_bytes_idx = der_bytes.find(akid_oid_bytes)
    if akid_oid_bytes_idx < 0:
        raise Exception("No AKID found")
    akid_val_idx = akid_oid_bytes_idx + len(akid_oid_bytes)
    akid_bytes = der_bytes[akid_val_idx:]
    (ident, akid, _) = readDERItem(akid_bytes)

    #print('akid = ',akid)
    #for i in akid[4:]:
    #    print(hex(i))

    return akid[4:]

def find_issue_date(der_bytes):
    issue_date_oid_bytes = bytearray([0x2B, 0x06, 0x01, 0x04, 0x01, 0x8B, 0x29, 0x0C, 0x09])
    issue_date_oid_bytes_idx = der_bytes.find(issue_date_oid_bytes)
    if issue_date_oid_bytes_idx < 0:
        raise Exception("No Issue date found")
    issue_date_val_idx = issue_date_oid_bytes_idx + len(issue_date_oid_bytes)
    issue_date_bytes = der_bytes[issue_date_val_idx:]
    (ident, issue_date, _) = readDERItem(issue_date_bytes)

    #print('issue date = ',issue_date)
    #for i in issue_date:
    #    print(hex(i))

    return issue_date

def createTOCEntry(args, dev, file_name):
    """Returns the TOC entry for the given input pfm file."""
    der_bytes = readPFM(file_name)

    try:
        akid = find_akid(der_bytes)
        issue_date = find_issue_date(der_bytes)
        # top-level collection
        (ident, value, der_bytes) = readDERItem(der_bytes)
        # TBS collection
        (ident, value, der_bytes) = readDERItem(value)
        # version
        (ident, value, der_bytes) = readDERItem(value)
        # serial number
        (serial_num, der_bytes) = readLargePositiveInteger(der_bytes)
        #print("Serial #", "".join(["%02x" % x for x in serial_num]))
    except Exception as err:
        print('Failed to parse "%s" for TOC entry' % (file_name))
        raise err

    print('-----'+file_name+'-----')
    # All these fields seem to be in big endian format in the pfm file
    #x = int.from_bytes(issue_date, "big")
    #print('issue date = ',x)
    #x = int.from_bytes(serial_num, "big")
    #print('serial_num = ',hex(x))
    #x = int.from_bytes(akid, "big")
    #print('akid = ',hex(x))

    id = issue_date + serial_num + akid
    sha256_hash = hashlib.sha256(id).hexdigest()
    #print('sha256_hash = ',sha256_hash)

    #Only first 8 bytes of the sha256 value is used as identifier
    hashed_id = sha256_hash[0:16] #The sha256 values are hex digits. 2 hex digits = 1 byte
    print('hashed_id = '+hex(int(hashed_id, 16)))
    len_hashed_id = int(len(hashed_id)/2)

    if len_hashed_id != IDENTIFIER_SIZE:
        raise Exception('hashed id should be exactly 8 bytes')

    if args.arch == "ipq5424":
        pad_len = TOC_ENTRY_IDENTIFIER_SIZE - IDENTIFIER_LEN - IDENTIFIER_SIZE
        attach_len = 0
    else:
        pad_len = TOC_ENTRY_IDENTIFIER_SIZE - IDENTIFIER_LEN - IDENTIFIER_SIZE - ATTACH_LEN - ATTACH_NUM
        attach_len = 1

    identifier = struct.pack('<I', len_hashed_id) + struct.pack('<Q', int(hashed_id, 16)) + struct.pack('<B', attach_len) + struct.pack('<B', dev) + struct.pack('%iB' % pad_len, *list([0] * pad_len))
    #print('pad_len = ',pad_len)
    #print('identifier = ',identifier)
    return identifier

def stripJson(args, device, pfm_files):
    dir = staging_dir + device

    if os.path.exists(dir):
        pass
    else:
        os.makedirs(dir)

    tmp_file_num = 1
    new_pfm_files = []
    for fname in pfm_files:
        fd = open(fname, 'r')
        lines = fd.readlines()
        index = 0
        for i in lines:
            if 0 == i.find("-----BEGIN CERTIFICATE-----"):
                break
            index += 1
        fd.close()
        path = os.path.join(dir, "tmp%d.pfm" % tmp_file_num)
        fd = open(path, 'w')
        for i in lines[index:]:
            fd.write(i)
        new_pfm_files.append(path)
        tmp_file_num += 1

    if (device == "soc"):
        args.soc = dir
    elif (device == "attach1"):
        args.attach1 = dir
    elif (device == "attach2"):
        args.attach2 = dir
    elif (device == "attach3"):
        args.attach3 = dir
    elif (device == "attach4"):
        args.attach4 = dir
    elif (device == "attach5"):
        args.attach5 = dir
    else:
        raise Exception('Wrong device %s' % device)

    print('license files updated in staging directory %s' % dir)

    return new_pfm_files

def getInputFiles(args, device):
    global max_licenses

    if (device == "soc"):
        path = args.soc
    elif (device == "attach1"):
        path = args.attach1
    elif (device == "attach2"):
        path = args.attach2
    elif (device == "attach3"):
        path = args.attach3
    elif (device == "attach4"):
        path = args.attach4
    elif (device == "attach5"):
        path = args.attach5


    if ((path is None) or (not os.path.exists(path))):
        print('License path for device(%s) is empty' % device)
        return []

    cwd = os.getcwd()
    os.chdir(path)
    file_names = os.popen("ls -t *.pfm 2> /dev/null").read().split()
    os.chdir(cwd)

    if (len(file_names) == 0):
        print('No pfm files found in input dir' + 'Generating an empty license store.')
        return []

    file_paths = [os.path.join(path, fname) for fname in file_names]
    pfm_files = filterUniqueFiles(file_paths)
    num_pfm_files = len(pfm_files)
    print('num_pfm_files = ',num_pfm_files)

    if num_pfm_files > max_licenses:
        raise Exception('Maximum of %d license files are supported.' % (max_licenses))

    if num_pfm_files == 0:
        print('No unique pfm files found in %s.' % path)
        print('Generating empty license store.')

    return stripJson(args, device, pfm_files)

def updateDataStoreHeaderFooter(partition):
    global data_store_hdr
    global data_store_ftr

    signature = DATA_STORE_MGR_SIGNATURE
    version = DATA_STORE_LATEST_VERSION
    age = 0
    write_method = WRITE_METHOD_SIMPLE_PING_PONG_TYPE
    cfg_data_size = 0
    max_payload_sectors = slots_per_store - (DATA_MGR_HDR + DATA_MGR_FTR)
    active_payload_sectors = 0
    sync_count = 0
    reserved0 = 0
    reserved1 = 0
    crc_32 = 0

    sync_count = sync_count + 1
    age = age + 1
    if age > MAX_AGE_VALUE:
        age = 0
    temp = struct.pack('<I', signature) + struct.pack('<H', version) + struct.pack('<H', age) + struct.pack('<H', write_method) + \
           struct.pack('<H', cfg_data_size) + struct.pack('<H', max_payload_sectors) + struct.pack('<H', active_payload_sectors) + \
           struct.pack('<I', sync_count) + struct.pack('<Q', reserved0) + struct.pack('<Q', reserved1)

    crc_32 = binascii.crc32(temp) & CRC32_SEED
    print('crc32 of hdr/ftr= ',hex(crc_32))

    Hdr = temp + struct.pack('<I', crc_32)

    #Hdr and Ftr has same data
    updatePartition(partition, int(getOffset(data_store_hdr, COPY_1), 16), Hdr)
    updatePartition(partition, int(getOffset(data_store_ftr, COPY_1), 16), Hdr)
    updatePartition(partition, int(getOffset(data_store_hdr, COPY_2), 16), Hdr)
    updatePartition(partition, int(getOffset(data_store_ftr, COPY_2), 16), Hdr)

def uefi(args):
    """Generates the uefi license store file."""
    if (args.output_file):
        FILE_NAME = args.output_file
    else:
        FILE_NAME = DEFAULT_FILE_NAME
    FILE_NAME = FILE_NAME + '.bin'
    partition = os.path.join(args.output_dir, FILE_NAME)
    createEmptyPartition(partition, (SLOT_SIZE * slots_per_store * NO_OF_COPIES))

    pfm_files = {}

    pfm_files[SOC] = getInputFiles(args, 'soc')
    if (args.arch != "ipq5424"):
        pfm_files[ATTACH1] = getInputFiles(args, 'attach1')
        pfm_files[ATTACH2] = getInputFiles(args, 'attach2')
        pfm_files[ATTACH3] = getInputFiles(args, 'attach3')
        pfm_files[ATTACH4] = getInputFiles(args, 'attach4')
        pfm_files[ATTACH5] = getInputFiles(args, 'attach5')

    Hdr = updateDataStoreHeaderFooter(partition)

    index = 1
    file_count = 0
    print(pfm_files)
    for dev in pfm_files.keys():
        for fname in pfm_files[dev]:
            index += 1
            file_size = os.path.getsize(fname)
            if (file_size == 0) or (file_size > PFM_FILE_MAXSIZE):
                print('\nSkipping "%s" file, it is either an empty file or it crosses the allowed max file size limit' % file)
                print('Received PFM file size - %d Bytes, Allowed max file size limit - %d Bytes\n' % (file_size, PFM_FILE_MAXSIZE))
                continue

            TOC_entry = createTOCEntry(args, dev, fname)
            updatePartition(partition, int(getOffset(TOC_INDEX, COPY_1), 16) + (file_count * TOC_ENTRY_IDENTIFIER_SIZE), TOC_entry)
            updatePartition(partition, int(getOffset(TOC_INDEX, COPY_2), 16) + (file_count * TOC_ENTRY_IDENTIFIER_SIZE), TOC_entry)
            data = struct.pack('<Q', file_size) + open(fname, "rb").read()
            n = getOffset(index, COPY_1)
            updatePartition(partition, int(getOffset(index, COPY_1), 16), data)
            updatePartition(partition, int(getOffset(index, COPY_2), 16), data)
            file_count += 1

    if (file_count == 0):
        raise Exception('No valid pfm files were found')

    print('Successfully generated a "%s" with %d pfmfiles in the following path. \n' % (FILE_NAME, file_count) +
          '%s' % str(args.output_dir))

def generatePartitionTbl(sps):
    offset_1 = 0
    offset_2 = sps * SLOT_SIZE
    for i in range(0, sps, 1):
        ptbl_copy1.update({i:hex(offset_1)})
        ptbl_copy2.update({i:hex(offset_2)})
        offset_1 += SLOT_SIZE
        offset_2 += SLOT_SIZE
    print('Parttion table copy 1:\n',ptbl_copy1)
    print('Parttion table copy 2:\n',ptbl_copy2)

def findPartitionInfo(args):
    global partition_size
    global store_size
    global slots_per_store
    global max_licenses
    global data_store_hdr
    global data_store_ftr

    if (args.arch == "ipq5424"):
        if (args.attach1 or args.attach2 or args.attach3 or args.attach4 or args.attach5):
            raise Exception('Target ipq5424 supports only SoC licenses.\n')

    if (args.flash == 'emmc'):
        #emmc erase size could be as low as 512 bytes. So check if the partition size is multiple of emmc erase size by converting it to bytes
        if ((args.size < EMMC_MIN_PART_SIZE) or ((args.size * 1024) % EMMC_ERASE_SIZE != 0)):
            raise Exception('Erase size of emmc is %d bytes. Partition size needs to be multiple of erase size. ' \
                            'Minimum emmc partition size is %dK bytes' % (EMMC_ERASE_SIZE, EMMC_MIN_PART_SIZE))
    elif (args.flash == 'nor'):
        if ((args.size < NO_OF_COPIES * NOR_ERASE_SIZE) or (args.size % NOR_ERASE_SIZE != 0)):
            raise Exception("Erase size of nor is %dK bytes. Partition size needs to be atleast 2 erase blocks and multiple of erase size." % NOR_ERASE_SIZE)
    elif (args.flash == 'nand2k'):
        if ((args.size < NO_OF_COPIES * NAND2K_ERASE_SIZE) or (args.size % NAND2K_ERASE_SIZE != 0)):
            raise Exception("Erase size of nand 2k is %dK bytes. Partition size needs to be atleast 2 erase blocks and multiple of erase size." % NAND2K_ERASE_SIZE)
    elif (args.flash == 'nand4k'):
        if ((args.size < NO_OF_COPIES * NAND4K_ERASE_SIZE) or (args.size % NAND4K_ERASE_SIZE != 0)):
            raise Exception("Erase size of nand 4k is %dK bytes. Partition size needs to be atleast 2 erase blocks and multiple of erase size." % NAND4K_ERASE_SIZE)
    else:
        raise Exception("Unsupported flash type")
        return

    partition_size = args.size * 1024
    print('partition_size = ',hex(partition_size))
    store_size = int(partition_size / NO_OF_COPIES)
    print('store_size = ',hex(store_size))
    slots_per_store = int(store_size / SLOT_SIZE)
    print('slots_per_store = ',slots_per_store)
    max_licenses = slots_per_store - (DATA_MGR_HDR + META_HDR + DATA_MGR_FTR)
    print('max_licenses supported = ',max_licenses)
    if (max_licenses > MAX_META):
        raise Exception("max licenses cannot exceed max meta's supported")
    data_store_hdr = 0
    data_store_ftr = slots_per_store - 1
    print('data_store_hdr loc = ',data_store_hdr)
    print('data_store_ftr loc = ',data_store_ftr)
    generatePartitionTbl(slots_per_store)

def main(args):
    """Parses the command line arguments and generates a UEFI based license store binary files."""
    print('qlstool launched as: "' + ' '.join(sys.argv) + '"\n')

    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    findPartitionInfo(args)

    uefi(args)

    if os.path.exists(staging_dir):
        os.popen('rm -rf %s' % staging_dir)
        print("staging directory cleared")

    return

def parseArgs(argv):
    # Specifying the usage and description.
    # noinspection PyTypeChecker
    qlsparser = argparse.ArgumentParser(description='Generates the UEFI based license store binary files.',
                                        formatter_class=argparse.RawDescriptionHelpFormatter,
                                        epilog=('\n'
                                                'This tool has been validated on python version 2.7 & 3.7.\n'
                                                'It is currently configured with the following parameters:-\n'
                                                '1) Generates the UEFI based license store binaries.\n'
                                                '2) Processes *.pfm files from the given input directory only.\n'
                                                '3) It does recognize duplicate pfm files, processes one file and '
                                                'skips the rest of duplicate files.\n'
                                                'UEFI:\n'
                                                '   a) Generates a qweslicstore.bin.\n'
                                                '   b) Supports 2 copies of Data Store.\n'
                                                '   c) Generates an empty qweslicstore.bin if there are 0 pfm files or if '
                                                'the number of the licenses exceeds licenses supported based on store size.\n'))
    # Specifying the version information.
    qlsparser.add_argument('--version', action='version',
                           version=__version__,
                           help='show the version number and exit')

    qlsparser.add_argument('--arch', type=str, help='Target SoC')

    # Specifying the SoC input location
    qlsparser.add_argument('--soc', metavar='<dir>',
                           help='directory containing pfm files for SOC')

    qlsparser.add_argument('--attach1', metavar='<dir>',
                            help='directory containing pfm files for attach 1')

    qlsparser.add_argument('--attach2', metavar='<dir>',
                           help='directory containing pfm files for attach 2')

    qlsparser.add_argument('--attach3', metavar='<dir>',
                           help='directory containing pfm files for attach 3')

    qlsparser.add_argument('--attach4', metavar='<dir>',
                           help='directory containing pfm files for attach 4')

    qlsparser.add_argument('--attach5', metavar='<dir>',
                           help='directory containing pfm files for attach 5')

    # Specifying the output location
    qlsparser.add_argument('-o', '--output_dir', metavar='<dir>',
                           help='directory to store output files. DEFAULT: "./"',
                           default=DEFAULT_QLS_DIR_PATH)

    #Specifying the output file name
    qlsparser.add_argument('-of', '--output_file', type=str,
                           help='file name to store output file.',
                           default=DEFAULT_FILE_NAME)

    # Specifying the flash type
    qlsparser.add_argument('-f', '--flash', type=str, choices=['nor', 'nand2k', 'nand4k', 'emmc'],
                           help='flash type for the binary')

    qlsparser.add_argument('-s', '--size', type=int, nargs='?', default=128, help='partition size in KB')

    qlsparser.add_argument('licenses', metavar='*.pfm', nargs='*',
                           help='license file to add to the store')

    return qlsparser.parse_args()


if __name__ == '__main__':
    try:
        main(parseArgs(sys.argv))
    except KeyboardInterrupt:
        print('Keyboard Interrupt Received. Exiting!')
        sys.exit(1)

    sys.exit(0)
