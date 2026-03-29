# ==========================================================================
# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: ISC
# ==========================================================================
import argparse
import os
import sys

import mbn_tools


# ------------------------------------------------------------------------------
# Action handlers
# ------------------------------------------------------------------------------
def handle_elf_cmpr_flags(args):
    if not os.path.isfile(args.elf_inp_file):
        raise RuntimeError("Input ELF file not present")

    return mbn_tools.set_compress_flag(
        args.elf_inp_file,
        args.elf_out_file
    )

# ------------------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------------------
def build_parser():
    p = argparse.ArgumentParser(description="ELF modification utility")

    p.add_argument(
        "-i", "--input-file",
        dest="elf_inp_file",
        required=True,
        help="Input ELF file",
    )
    p.add_argument(
        "-o", "--output-file",
        dest="elf_out_file",
        required=True,
        help="Output ELF file",
    )

    # Action flags (extendable)
    p.add_argument(
        "-z", "--elf-cmpr-flags",
        dest="elf_cmpr_flags",
        action="store_true",
        help="Set ELF compression flags (lzma+loos)",
    )

    return p


ACTIONS = {
    "elf_cmpr_flags": handle_elf_cmpr_flags,
    # future actions
    #"new_flag": handle_new_flag,
}

# ------------------------------------------------------------------------------
# Arguments dispatch logic
# ------------------------------------------------------------------------------
def dispatch(args):
    selected = [k for k in ACTIONS if getattr(args, k, False)]

    if not selected:
        raise RuntimeError("No operation specified")

    for key in selected:
        handler = ACTIONS[key]
        rc = handler(args)
        if rc:
            raise RuntimeError("Operation Failed " + handler.__name__)

    return 0

# ------------------------------------------------------------------------------
# Main Logic
# ------------------------------------------------------------------------------
def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        return dispatch(args)
    except RuntimeError as e:
        sys.stderr.write("Error: %s\n" % e)
        return 1


if __name__ == '__main__':
    sys.exit(main())
