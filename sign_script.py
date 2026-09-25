#!/usr/bin/env python3
# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: ISC

"""Sign mapped images from one or more files or folders.

Procedure:
  1. Ensure Python 3, sectools, objcopy, ld, and readelf are available.
  2. Provide one security profile after each input.
  3. Use absolute paths for security profiles.

Examples:
  python3 sign_script.py \
      /path/to/folder1 --security-profile /absolute/path/profile1.xml \
      /path/to/folder2 --security-profile /absolute/path/profile2.xml

  python3 sign_script.py \
      /path/to/folder1 --security-profile /absolute/path/profile1.xml \
      --output-dir /path/to/output1 \
      /path/to/folder2 --security-profile /absolute/path/profile2.xml \
      --output-dir /path/to/output2

Without -o, signed images replace the originals. Only exact basenames listed
in IMAGE_SIGN_ID_MAP are signed; other files are skipped. HLOS and ROOTFS
must be supplied in the same invocation.
"""

import os
import argparse
import subprocess
import sys

# Resolve the profile relative to this script.
CDIR = os.path.dirname(os.path.abspath(__file__))

# Signing configuration.
SECTOOLS = "/pkg/sectools/v2/latest/Linux/sectools"
SIGNING_MODE = "TEST"
SIGNATURE_FORMAT = "ECDSA-SHA384-SECP384R1"
ROOT_CERTIFICATE_COUNT = "1"
ROOT_CERTIFICATE_INDEX = "0"
KERNEL_LOAD_ADDRESS = "0x84000000"


# Exact image basename to SIGN_ID mapping.
IMAGE_SIGN_ID_MAP = {
    "u-boot-spl.mbn":        "XBL",
    "QCLib.mbn":              "QCLIB-DDR",
    "qcconfig-DB-HM01.1_1024M16_DDR4.elf": "QCLIB-DDR",
    "bl31.mbn":               "ATF",
    "tee-raw.mbn":            "OPTEE",
    "openwrt-ipq5210-generic-norplusnand-u-boot-rdp503.mbn": "APPSBL",
    "tmel-ipq52xx-patch.elf": "TMEL-RAM-PATCH",
    "openwrt-ipq52xx-generic-qcom_rdp497-fit-uImage.itb": "HLOS",
    "openwrt-ipq52xx-generic-squashfs-root.img":        "ROOTFS",
}


def resolve_images(paths):
    """Resolve image paths to SIGN_IDs."""
    resolved = []
    unmapped = []
    for path in paths:
        base = os.path.basename(path)
        sign_id = IMAGE_SIGN_ID_MAP.get(base)
        if sign_id is None:
            unmapped.append(base)
            continue
        resolved.append((path, base, sign_id))
    return resolved, unmapped


def sign_one(path, base, sign_id, security_profile, output_dir=None):
    """Sign one image."""
    if not os.path.isfile(path):
        print("ERROR: input image not found: %s" % path)
        return False, None

    out_dir = output_dir or os.path.dirname(os.path.abspath(path))
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    outfile = os.path.join(out_dir, base)
    sectools_outfile = outfile if output_dir else outfile + ".signing-tmp"

    cmd = [SECTOOLS, "secure-image", path,
          "--outfile", sectools_outfile,
          "--image-id", sign_id,
          "--sign",
          "--security-profile", security_profile,
          "--signing-mode", SIGNING_MODE,
          "--signature-format", SIGNATURE_FORMAT,
          "--root-certificate-index", ROOT_CERTIFICATE_INDEX,
          "--root-certificate-count", ROOT_CERTIFICATE_COUNT]

    print("signing %s (sign_id=%s) -> %s" % (base, sign_id, outfile))
    print("+ " + " ".join(cmd))

    try:
        rc = subprocess.call(cmd)
    except OSError as e:
        print("ERROR: could not run sectools (%s) for image=%s sign_id=%s: %s"
             % (SECTOOLS, base, sign_id, e))
        return False, None
    if rc != 0:
        print("ERROR: sectools failed (rc=%d) for image=%s sign_id=%s"
             % (rc, base, sign_id))
        return False, None
    if not os.path.isfile(sectools_outfile):
        print("ERROR: sectools exited 0 for %s but %s was not created"
             % (base, outfile))
        return False, None

    if not output_dir:
        os.replace(sectools_outfile, outfile)

    print("SIGNED_OUTPUT: %s" % outfile)
    return True, outfile


def _run(cmd, cwd=None):
    print("+ " + " ".join(cmd))
    try:
        return subprocess.call(cmd, cwd=cwd)
    except OSError as e:
        print("ERROR: could not run %s: %s" % (cmd[0], e))
        return None


def _wrap_as_elf(bin_path, ld_script_text, elf_path, work_dir):
    """Wrap a binary as an ELF."""
    ld_script = os.path.join(work_dir, os.path.basename(elf_path) + ".ld")
    obj_o = os.path.join(work_dir, os.path.basename(elf_path) + ".o")
    try:
        with open(ld_script, "w") as f:
            f.write(ld_script_text)
        rc = _run(["objcopy", "-I", "binary", "-O", "elf32-i386",
                  "--binary-architecture", "i386", bin_path, obj_o],
                 cwd=work_dir)
        if rc != 0:
            print("ERROR: objcopy failed (rc=%s) wrapping %s" % (rc, bin_path))
            return False
        rc = _run(["ld", "-m", "elf_i386", obj_o, "-T", ld_script,
                  "-o", elf_path], cwd=work_dir)
        if rc != 0:
            print("ERROR: ld failed (rc=%s) wrapping %s" % (rc, bin_path))
            return False
        return True
    finally:
        for tmp in (ld_script, obj_o):
            if os.path.isfile(tmp):
                os.remove(tmp)


def sign_kernel_image(path, base, security_profile, output_dir=None):
    """Wrap and sign the kernel image."""
    path = os.path.abspath(path)
    if not os.path.isfile(path):
        print("ERROR: input image not found: %s" % path)
        return False, None

    work_dir = os.path.dirname(os.path.abspath(path))
    out_dir = output_dir or work_dir
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    outfile = os.path.join(out_dir, base)
    sectools_outfile = outfile if output_dir else outfile + ".signing-tmp"
    elf_path = os.path.join(work_dir, os.path.splitext(base)[0] + ".elf")

    print("signing %s (sign_id=HLOS) -> %s" % (base, outfile))
    try:
        if not _wrap_as_elf(path,
                            "SECTIONS\n{\n. = %s;\n.data : {\n*(.data)\n}\n}\n" % KERNEL_LOAD_ADDRESS,
                            elf_path, work_dir):
            return False, None

        cmd = [SECTOOLS, "secure-image", elf_path,
              "--outfile", sectools_outfile,
              "--image-id", "HLOS",
              "--sign",
              "--security-profile", security_profile,
              "--signing-mode", SIGNING_MODE,
              "--signature-format", SIGNATURE_FORMAT,
              "--root-certificate-index", ROOT_CERTIFICATE_INDEX,
              "--root-certificate-count", ROOT_CERTIFICATE_COUNT]
        rc = _run(cmd)
        if rc != 0:
            print("ERROR: sectools failed (rc=%s) for image=%s sign_id=HLOS" % (rc, base))
            return False, None
        if not os.path.isfile(sectools_outfile):
            print("ERROR: sectools exited 0 for %s but %s was not created" % (base, outfile))
            return False, None

        if not output_dir:
            os.replace(sectools_outfile, outfile)

        print("SIGNED_OUTPUT: %s" % outfile)
        return True, outfile
    finally:
        if os.path.isfile(elf_path):
            os.remove(elf_path)


def _find_rootfs_data_offset(path):
    """Find the rootfs data offset."""
    size = os.path.getsize(path)
    block = 0
    with open(path, "rb") as f:
        while True:
            pos = block * 65536
            if pos >= size:
                return None
            f.seek(pos)
            word = f.read(4)
            if len(word) == 4 and word.hex() in ("deadc0de", "19852003"):
                return pos
            block += 1


def _first_load_segment_offset(elf_path):
    """Find the last ELF LOAD segment offset."""
    try:
        out = subprocess.check_output(["readelf", "-l", elf_path]).decode()
    except (subprocess.CalledProcessError, OSError) as e:
        print("ERROR: readelf failed for %s: %s" % (elf_path, e))
        return None
    offset = None
    for line in out.splitlines():
        parts = line.split()
        if parts and parts[0] == "LOAD":
            try:
                offset = int(parts[1], 16)
            except (IndexError, ValueError):
                continue
    return offset


def sign_rootfs_image(path, base, kernel_signed_itb, security_profile,
                      output_dir=None):
    """Wrap and sign rootfs, then append it to the signed kernel."""
    path = os.path.abspath(path)
    if not os.path.isfile(path):
        print("ERROR: input image not found: %s" % path)
        return False, None

    work_dir = os.path.dirname(os.path.abspath(path))
    out_dir = output_dir or work_dir
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    offset = _find_rootfs_data_offset(path)
    if offset is None:
        print("ERROR: could not find rootfs_data start magic in %s" % base)
        return False, None
    print("rootfs data blockoffset: %d" % offset)

    stem = os.path.splitext(base)[0]
    stripped = os.path.join(work_dir, stem + "_stripped.img")
    stripped_elf = os.path.join(work_dir, stem + "_stripped.elf")
    signed_stripped_elf = os.path.join(out_dir, os.path.basename(stripped_elf))
    signed_img = os.path.join(out_dir, base)
    signed_img_tmp = signed_img if output_dir else signed_img + ".signing-tmp"

    print("signing %s (sign_id=ROOTFS) -> %s" % (base, signed_stripped_elf))
    try:
        with open(path, "rb") as src, open(stripped, "wb") as dst:
            dst.write(src.read(offset))

        if not _wrap_as_elf(stripped,
                            "SECTIONS\n{\n. = 0x90000000;\n.data : {\n*(.data)\n}\n}\n",
                            stripped_elf, work_dir):
            return False, None

        cmd = [SECTOOLS, "secure-image", stripped_elf,
              "--outfile", signed_stripped_elf,
              "--image-id", "ROOTFS",
              "--sign",
              "--security-profile", security_profile,
              "--signing-mode", SIGNING_MODE,
              "--signature-format", SIGNATURE_FORMAT,
              "--root-certificate-index", ROOT_CERTIFICATE_INDEX,
              "--root-certificate-count", ROOT_CERTIFICATE_COUNT]
        rc = _run(cmd)
        if rc != 0:
            print("ERROR: sectools failed (rc=%s) for image=%s sign_id=ROOTFS" % (rc, base))
            return False, None
        if not os.path.isfile(signed_stripped_elf):
            print("ERROR: sectools exited 0 for %s but %s was not created"
                 % (base, signed_stripped_elf))
            return False, None

        size_hdr_n_hash = _first_load_segment_offset(signed_stripped_elf)
        if size_hdr_n_hash is None:
            return False, None
        with open(signed_stripped_elf, "rb") as f:
            header_and_hash = f.read(size_hdr_n_hash)
        with open(kernel_signed_itb, "ab") as f:
            f.write(header_and_hash)
        print("appended %d byte(s) of header+hash from %s onto %s"
             % (size_hdr_n_hash, base, kernel_signed_itb))

        with open(signed_stripped_elf, "rb") as src, open(signed_img_tmp, "wb") as dst:
            dst.write(src.read())

        if not output_dir:
            os.replace(signed_img_tmp, signed_img)

        print("SIGNED_OUTPUT: %s" % signed_stripped_elf)
        print("SIGNED_OUTPUT: %s" % signed_img)
        return True, signed_stripped_elf
    finally:
        for tmp in (stripped, stripped_elf):
            if os.path.isfile(tmp):
                os.remove(tmp)


def _expand_inputs(inputs):
    paths = []
    for item in inputs:
        if os.path.isdir(item):
            paths.extend(os.path.join(item, name) for name in sorted(os.listdir(item))
                         if os.path.isfile(os.path.join(item, name)))
        else:
            paths.append(item)
    return paths


def _parse_arguments(argv):
    parser = argparse.ArgumentParser(
        description="Sign mapped images from one or more files or folders.")

    input_profiles = []
    index = 0
    while index < len(argv):
        item = argv[index]
        if item in ("-h", "--help"):
            parser.print_help()
            raise SystemExit(0)
        if item in ("-o", "--output-dir"):
            parser.error("%s must follow an input and its security profile" % item)
        if item.startswith("-"):
            parser.error("unrecognized argument: %s" % item)

        folder = item
        if index + 2 >= len(argv) or argv[index + 1] != "--security-profile":
            parser.error("each input must be followed by --security-profile PATH")
        profile = argv[index + 2]
        index += 3
        output_dir = None
        if index < len(argv) and argv[index] in ("-o", "--output-dir"):
            if index + 1 >= len(argv):
                parser.error("argument %s: expected a directory" % argv[index])
            output_dir = argv[index + 1]
            index += 2
        input_profiles.append((folder, profile, output_dir))

    if not input_profiles:
        parser.error("at least one input and security profile are required")
    return input_profiles


def main(argv):
    input_profiles = _parse_arguments(argv)
    inputs = []
    profile_by_input = {}
    output_by_input = {}
    for input_path, profile, output_arg in input_profiles:
        for path in _expand_inputs([input_path]):
            inputs.append(path)
            profile_by_input[path] = profile
            output_by_input[path] = (os.path.abspath(output_arg)
                                     if output_arg else None)

    for output_dir in set(output_by_input.values()) - {None}:
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

    try:
        resolved, _ = resolve_images(inputs)
    except ValueError as e:
        print("ERROR: %s" % e)
        return 1

    if not resolved:
        return 0

    rootfs_entry = next((r for r in resolved if r[2] == "ROOTFS"), None)
    kernel_entry = next((r for r in resolved if r[2] == "HLOS"), None)
    if rootfs_entry and not kernel_entry:
        print("ERROR: rootfs signing (%s) requires the matching kernel "
             "image (SIGN_ID=HLOS) in the same invocation - rootfs is "
             "appended onto the freshly-signed kernel .itb, never a stale "
             "one from an earlier run." % rootfs_entry[1])
        return 1

    print("Resolved image -> SIGN_ID mapping:")
    for _, base, sign_id in resolved:
        print("  %s -> %s" % (base, sign_id))

    failures = []
    successes = 0
    kernel_signed_itb = None

    # Sign HLOS first because ROOTFS is appended to it.
    ordered = resolved
    if kernel_entry:
        ordered = [kernel_entry] + [r for r in resolved if r is not kernel_entry]

    for path, base, sign_id in ordered:
        if sign_id == "HLOS":
            output_dir = output_by_input[path]
            ok, signed_itb = sign_kernel_image(path, base,
                                               profile_by_input[path], output_dir)
            if ok:
                kernel_signed_itb = signed_itb
        elif sign_id == "ROOTFS":
            if kernel_signed_itb is None:
                print("ERROR: skipping rootfs signing for %s - kernel "
                     "signing did not succeed, nothing to append onto." % base)
                ok = False
            else:
                output_dir = output_by_input[path]
                ok, _ = sign_rootfs_image(path, base, kernel_signed_itb,
                                          profile_by_input[path], output_dir)
        else:
            output_dir = output_by_input[path]
            ok, _ = sign_one(path, base, sign_id, profile_by_input[path],
                             output_dir)

        if ok:
            successes += 1
        else:
            failures.append((base, sign_id))

    if failures:
        print("ERROR: %d image(s) failed to sign:" % len(failures))
        for base, sign_id in failures:
            print("  %s (SIGN_ID=%s)" % (base, sign_id))
        return 1

    print("signed %d image(s) successfully" % successes)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
