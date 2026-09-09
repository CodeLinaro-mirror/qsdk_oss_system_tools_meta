#!/usr/bin/env python3
# ==========================================================================
# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: ISC
# ==========================================================================
#
# Assemble an IPQ5210 MVEW (Multi-Version ELF Wrapper) outer wrapper from
# real sectools-signed kernel/rootfs output, matching the layout that
# arch/arm/mach-ipq/cmd_bootipq.c's is_mvew_wrapper() / parse_elf_image_phdr_mvew()
# expect: one Elf32_Ehdr + 6 fixed Elf32_Phdrs (marker, kernel-v7-meta,
# kernel-v8-meta, itb, rootfs-v7-meta, rootfs-v8-meta), followed by the
# concatenated blob data.
#
# Kernel and rootfs are both legacy self-contained blobs: a small ELF
# metadata header (parsed the same way as parse_elf_image_phdr(),
# NO_OF_PROGRAM_HDRS=3) immediately followed by the raw payload. This tool
# SPLITS both the same way, embedding only the metadata header in the
# wrapper and discarding the payload here:
#   - Kernel (--kernel-v7-signed/--kernel-v8-signed): the metadata header
#     goes in its own kernel-v7/v8-meta Phdr, and the itb payload (shared,
#     since it's version-independent) goes in the single itb Phdr.
#   - Rootfs (--rootfs-v7-signed/--rootfs-v8-signed): only the metadata
#     header goes in its own rootfs-v7/v8-meta Phdr. authenticate_rootfs_
#     elf_ipc_v2()/_v3() (cmd_bootipq.c) re-parse just that header at boot
#     to recover img_load_addr/img_size, then fetch the real rootfs payload
#     via copy_rootfs() from the dedicated rootfs flash partition -- they
#     never read payload bytes from the MVEW wrapper itself. The actual
#     rootfs payload must already be flashed to that partition through the
#     normal (non-MVEW) rootfs flashing flow; this tool does not write it.
#
# This tool does not sign or authenticate anything -- inputs must already
# be real sectools-signed output (or dummy bytes, for structural-only
# testing of the U-Boot parser).

import argparse
import struct
import sys

ELF32_EHDR_FMT = "<16sHHIIIIIHHHHHH"
ELF32_EHDR_SIZE = struct.calcsize(ELF32_EHDR_FMT)
ELF32_PHDR_FMT = "<8I"
ELF32_PHDR_SIZE = struct.calcsize(ELF32_PHDR_FMT)

NO_OF_PROGRAM_HDRS = 3     # legacy self-contained blob's own phdr count
MAX_PROGRAM_HDRS = 6       # MVEW outer wrapper's phdr count
HEADER_SIZE = ELF32_EHDR_SIZE + MAX_PROGRAM_HDRS * ELF32_PHDR_SIZE

MVEW_SECTION_PAD = 4096    # zero-padding inserted between adjacent blob segments;
                           # each segment's offset/size is self-describing in its
                           # own Phdr (never adjacency-based), so this only exists
                           # to keep segments independent of each other's exact size

ELFMAG = b"\x7fELF"
ELFCLASS32 = 1
ELFDATA2LSB = 1
EV_CURRENT = 1
ET_EXEC = 2
EM_ARM = 40

PT_NULL = 0
PT_LOAD = 1
PF_MASKOS = 0x0FF00000

MVEW_WRAPPER_FLAG = 0xA << 20

HASH_TARGET_KERNEL = 0
HASH_TARGET_ROOTFS = 1


def hash_p_flag(target, ver):
    return (target << 24) | (ver << 20)


HASH_P_FLAG_MBN_V7 = hash_p_flag(HASH_TARGET_KERNEL, 7)
HASH_P_FLAG_MBN_V8 = hash_p_flag(HASH_TARGET_KERNEL, 8)
HASH_P_FLAG_ROOTFS_MBN_V7 = hash_p_flag(HASH_TARGET_ROOTFS, 7)
HASH_P_FLAG_ROOTFS_MBN_V8 = hash_p_flag(HASH_TARGET_ROOTFS, 8)


def pack_ehdr():
    e_ident = ELFMAG + bytes([ELFCLASS32, ELFDATA2LSB, EV_CURRENT]) + b"\x00" * 9
    return struct.pack(
        ELF32_EHDR_FMT,
        e_ident,
        ET_EXEC,
        EM_ARM,
        EV_CURRENT,
        0,                  # e_entry
        ELF32_EHDR_SIZE,    # e_phoff
        0,                  # e_shoff
        0,                  # e_flags
        ELF32_EHDR_SIZE,    # e_ehsize
        ELF32_PHDR_SIZE,    # e_phentsize
        MAX_PROGRAM_HDRS,   # e_phnum
        0, 0, 0,            # e_shentsize, e_shnum, e_shstrndx
    )


def pack_phdr(p_type, p_offset, p_paddr, p_filesz, p_flags):
    return struct.pack(
        ELF32_PHDR_FMT,
        p_type,
        p_offset,
        p_paddr,   # p_vaddr, mirrors p_paddr; unused by the parser
        p_paddr,
        p_filesz,
        p_filesz,  # p_memsz
        p_flags,
        4,         # p_align
    )


def placeholder_phdr():
    return pack_phdr(PT_NULL, 0, 0, 0, 0)


def read_blob(path):
    if path is None:
        return None
    with open(path, "rb") as f:
        return f.read()


def split_legacy_signed_blob(data, label):
    """Split a legacy self-contained signed blob (small ELF metadata
    header immediately followed by the real payload) into (metadata_bytes,
    payload_bytes, load_addr), replicating parse_elf_image_phdr()'s exact
    NO_OF_PROGRAM_HDRS=3 / first-PT_LOAD-wins logic (cmd_bootipq.c)."""
    if len(data) < ELF32_EHDR_SIZE:
        sys.exit(f"error: {label} is too short to be an ELF (signed) blob")

    ehdr = struct.unpack(ELF32_EHDR_FMT, data[:ELF32_EHDR_SIZE])
    e_ident, e_type, e_phoff = ehdr[0], ehdr[1], ehdr[5]
    if e_ident[:4] != ELFMAG:
        sys.exit(f"error: {label} is not an ELF (signed) blob -- is it already-split/raw?")
    if e_type != ET_EXEC:
        sys.exit(f"error: {label} has e_type != ET_EXEC, not a valid signed blob")

    for i in range(NO_OF_PROGRAM_HDRS):
        off = e_phoff + i * ELF32_PHDR_SIZE
        p_type, p_offset, p_vaddr, p_paddr, p_filesz, p_memsz, p_flags, p_align = \
            struct.unpack(ELF32_PHDR_FMT, data[off:off + ELF32_PHDR_SIZE])
        if p_type == PT_LOAD:
            metadata = data[:p_offset]
            payload = data[p_offset:p_offset + p_filesz]
            return metadata, payload, p_paddr

    sys.exit(f"error: {label} has no PT_LOAD segment in its first {NO_OF_PROGRAM_HDRS} phdrs")


def build(args):
    kernel_meta = {}   # 'v7'/'v8' -> metadata bytes
    derived = {}       # 'v7'/'v8' -> (itb payload bytes, load_addr)

    for ver, path, optname in (("v7", args.kernel_v7_signed, "--kernel-v7-signed"),
                                ("v8", args.kernel_v8_signed, "--kernel-v8-signed")):
        if path is None:
            continue
        blob = read_blob(path)
        meta, payload, load_addr = split_legacy_signed_blob(blob, optname)
        kernel_meta[ver] = meta
        derived[ver] = (payload, load_addr)
        print(f"split {optname}: metadata={len(meta)} bytes, itb payload={len(payload)} bytes, "
              f"load_addr=0x{load_addr:x}")

    if not kernel_meta:
        sys.exit("error: need at least one of --kernel-v7-signed / --kernel-v8-signed")

    if "v7" in derived and "v8" in derived and derived["v7"][0] != derived["v8"][0]:
        print("warning: v7-signed and v8-signed itb payloads differ byte-for-byte; "
              "using the v7 payload for the shared itb slot", file=sys.stderr)

    fallback_payload, fallback_load_addr = derived.get("v7") or derived.get("v8")
    itb = read_blob(args.itb) if args.itb else fallback_payload
    itb_load_addr = args.itb_load_addr if args.itb_load_addr is not None else fallback_load_addr

    rootfs_meta = {}   # 'v7'/'v8' -> metadata bytes

    for ver, path, optname in (("v7", args.rootfs_v7_signed, "--rootfs-v7-signed"),
                                ("v8", args.rootfs_v8_signed, "--rootfs-v8-signed")):
        if path is None:
            continue
        blob = read_blob(path)
        meta, payload, load_addr = split_legacy_signed_blob(blob, optname)
        rootfs_meta[ver] = meta
        print(f"split {optname}: metadata={len(meta)} bytes, rootfs payload={len(payload)} bytes "
              "(payload not embedded -- must already be on the rootfs flash partition)")

    rootfs_v7 = rootfs_meta.get("v7")
    rootfs_v8 = rootfs_meta.get("v8")

    marker = pack_phdr(PT_NULL, 0, 0, 0, MVEW_WRAPPER_FLAG)

    offset = HEADER_SIZE
    layout = []      # (label, offset, size)

    def place(label, data):
        nonlocal offset
        if data is None:
            return None
        if layout:
            offset += MVEW_SECTION_PAD
        off = offset
        offset += len(data)
        layout.append((label, off, len(data)))
        return off

    kv7_off = place("kernel-v7-meta", kernel_meta.get("v7"))
    kv8_off = place("kernel-v8-meta", kernel_meta.get("v8"))
    itb_off = place("itb", itb)
    rv7_off = place("rootfs-v7-meta", rootfs_v7)
    rv8_off = place("rootfs-v8-meta", rootfs_v8)

    phdrs = [marker]

    phdrs.append(
        pack_phdr(PT_NULL, kv7_off, 0, len(kernel_meta["v7"]), HASH_P_FLAG_MBN_V7)
        if "v7" in kernel_meta else placeholder_phdr()
    )
    phdrs.append(
        pack_phdr(PT_NULL, kv8_off, 0, len(kernel_meta["v8"]), HASH_P_FLAG_MBN_V8)
        if "v8" in kernel_meta else placeholder_phdr()
    )
    phdrs.append(
        pack_phdr(PT_LOAD, itb_off, itb_load_addr, len(itb), 0)
    )
    phdrs.append(
        pack_phdr(PT_NULL, rv7_off, 0, len(rootfs_v7), HASH_P_FLAG_ROOTFS_MBN_V7)
        if rootfs_v7 is not None else placeholder_phdr()
    )
    phdrs.append(
        pack_phdr(PT_NULL, rv8_off, 0, len(rootfs_v8), HASH_P_FLAG_ROOTFS_MBN_V8)
        if rootfs_v8 is not None else placeholder_phdr()
    )

    image = bytearray(offset)
    image[:HEADER_SIZE] = pack_ehdr() + b"".join(phdrs)

    blobs = {
        "kernel-v7-meta": kernel_meta.get("v7"),
        "kernel-v8-meta": kernel_meta.get("v8"),
        "itb": itb,
        "rootfs-v7-meta": rootfs_v7,
        "rootfs-v8-meta": rootfs_v8,
    }
    for label, off, size in layout:
        image[off:off + size] = blobs[label]
    image = bytes(image)

    with open(args.output, "wb") as f:
        f.write(image)

    print(f"wrote {args.output}: {len(image)} bytes total, "
          f"{HEADER_SIZE}-byte header + {len(image) - HEADER_SIZE} bytes of blobs+padding "
          f"({MVEW_SECTION_PAD}-byte pad between adjacent segments)")
    for label, off, size in layout:
        print(f"  {label:16s} offset=0x{off:x} size=0x{size:x}")
    print(f"  {'itb load addr':16s} 0x{itb_load_addr:x}")
    if rootfs_v7 is None and rootfs_v8 is None:
        print("  (no rootfs signed image supplied -- rootfs slots are inert placeholders,"
              " has_rootfs_meta will read false for both MBN versions)")

    verify(args.output)


def verify(path):
    """Mimic is_mvew_wrapper()/parse_elf_image_phdr_mvew() against the
    just-written file, for both MBN versions, so the packer's own output
    can be sanity-checked without a cross-compiler or real U-Boot."""
    with open(path, "rb") as f:
        data = f.read(HEADER_SIZE)

    ehdr = struct.unpack(ELF32_EHDR_FMT, data[:ELF32_EHDR_SIZE])
    e_ident, e_type, e_phoff = ehdr[0], ehdr[1], ehdr[5]
    if e_ident[:4] != ELFMAG or e_type != ET_EXEC:
        print("verify: FAILED -- not a well-formed outer wrapper")
        return

    phdr_bytes = data[e_phoff:e_phoff + MAX_PROGRAM_HDRS * ELF32_PHDR_SIZE]
    phdrs = [
        struct.unpack(ELF32_PHDR_FMT, phdr_bytes[i * ELF32_PHDR_SIZE:(i + 1) * ELF32_PHDR_SIZE])
        for i in range(MAX_PROGRAM_HDRS)
    ]

    p_type0, p_flags0 = phdrs[0][0], phdrs[0][6]
    if not (p_type0 == PT_NULL and (p_flags0 & PF_MASKOS) == MVEW_WRAPPER_FLAG):
        print("verify: FAILED -- phdr[0] is not MVEW-tagged, is_mvew_wrapper() would return false")
        return

    print("verify: is_mvew_wrapper() -> true")

    for mbn_version, wanted, wanted_rootfs in (
        (7, HASH_P_FLAG_MBN_V7, HASH_P_FLAG_ROOTFS_MBN_V7),
        (8, HASH_P_FLAG_MBN_V8, HASH_P_FLAG_ROOTFS_MBN_V8),
    ):
        load_phdr = hash_phdr = rootfs_hash_phdr = None
        for p_type, p_offset, p_vaddr, p_paddr, p_filesz, p_memsz, p_flags, p_align in phdrs:
            if p_type == PT_LOAD:
                load_phdr = (p_offset, p_paddr, p_filesz)
            elif p_type == PT_NULL and (p_flags & PF_MASKOS) == wanted:
                hash_phdr = (p_offset, p_filesz)
            elif p_type == PT_NULL and (p_flags & PF_MASKOS) == wanted_rootfs:
                rootfs_hash_phdr = (p_offset, p_filesz)

        print(f"  required_mbn_version={mbn_version}:")
        if not hash_phdr:
            print("    no metadata segment for this MBN version -- parse_elf_image_phdr_mvew() would return -EINVAL")
            continue
        if not load_phdr:
            print("    no .itb (PT_LOAD) segment -- parse_elf_image_phdr_mvew() would return -EINVAL")
            continue
        print(f"    meta_flash_offset=0x{hash_phdr[0]:x} img_offset(provisional)=0x{hash_phdr[1]:x}")
        print(f"    itb_flash_offset=0x{load_phdr[0]:x} img_load_addr=0x{load_phdr[1]:x} img_size=0x{load_phdr[2]:x}")
        if rootfs_hash_phdr:
            print(f"    has_rootfs_meta=true rootfs_meta_flash_offset=0x{rootfs_hash_phdr[0]:x}")
        else:
            print("    has_rootfs_meta=false")


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--kernel-v7-signed",
                     help="sectools-signed kernel output for MBN v7 (self-contained: "
                          "metadata header + itb payload); this tool splits it")
    ap.add_argument("--kernel-v8-signed",
                     help="sectools-signed kernel output for MBN v8, same shape as v7")
    ap.add_argument("--itb",
                     help="override: raw itb payload, if you already have it split out; "
                          "default is the payload split from --kernel-v7/v8-signed")
    ap.add_argument("--itb-load-addr", type=lambda x: int(x, 0), default=None,
                     help="override: DRAM load address for the itb; default is the "
                          "load address read from --kernel-v7/v8-signed's own PT_LOAD phdr")
    ap.add_argument("--rootfs-v7-signed",
                     help="sectools-signed rootfs output for MBN v7 (self-contained: "
                          "metadata header + payload); this tool splits it and embeds "
                          "only the metadata header -- the payload must already be "
                          "flashed to the rootfs partition. Omit for a kernel-only image")
    ap.add_argument("--rootfs-v8-signed",
                     help="sectools-signed rootfs output for MBN v8, same shape as v7")
    ap.add_argument("-o", "--output", required=True, help="output MVEW image path")
    build(ap.parse_args())


if __name__ == "__main__":
    main()
