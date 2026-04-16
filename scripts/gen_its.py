# ==========================================================================
# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: ISC
# ==========================================================================
# gen_its.py - A script to generate FIT (Flattened Image Tree) images from ELF/MBN files
# using a template-based approach.
#
# Example Usage:
# -------------
# Using conditional template :
# python gen_its.py --template template.its \
#                  --arch ipq9650 \
#                  --qclib_path qclib.elf \
#                  --qcconfig_path qcconfig.elf \
#                  --tfa_bl31.mbn \
#                  --uboot_path openwrt-ipq5200-generic-mmc-u-boot.mbn \
#                  --optee_path tee-pager_v2.mbn \
#                  --dtb_path u-boot.dtb \
#                  --dpr dpr.elf \
#                  --output ./new_out/boot_loader.img
#
# This will create boot_loader.its and boot_loader.img in the ./new_out directory
#
# Note: All component paths (qclib_path, qcconfig_path, tfa_bl31_path, uboot_path, optee_path) are required.
# Optional paths: --dtb_path (Device Tree Blob), --dpr (DPR ELF, loaded as a whole image before qcconfig).
# The script will always process templates with conditional statements (#define) and replace placeholders.
# This script is compatible with both Python 2.7 and Python 3.

from __future__ import print_function

import os
import argparse
import mbn_tools
import subprocess
import shutil
import re
import sys
import errno

class TemplateManager:
    """
    Unified class for handling ITS template operations, supporting both conditional and non-conditional templates.
    """
    def __init__(self, template_path, output_path=None, temp_files_list=None):
        """
        Initialize the TemplateManager.

        Args:
            template_path: Path to the template ITS file
            output_path: Path to save the processed ITS file (optional for non-conditional templates)
            temp_files_list: List to track temporary files created during execution (optional)
        """
        self.template_path = template_path
        self.output_path = output_path
        self.template_content = None
        self.component_data = {}
        self.component_defines = {
            'HAVE_QCLIB': 0,
            'HAVE_QCCONFIG': 0,
            'HAVE_TFA_BL31': 0,
            'HAVE_UBOOT': 0,
            'HAVE_OPTEE': 0,
            'HAVE_FDT': 0,
            'HAVE_DPR': 0
        }
        self.placeholders = {}
        self.is_conditional = True
        self.temp_files_list = temp_files_list

    def load_template(self):
        """
        Load the template ITS file.

        Returns:
            bool: True if the operation was successful, False otherwise
        """
        try:
            with open(self.template_path, 'r') as f:
                self.template_content = f.read()
            return True
        except (IOError, OSError) as e:
            return handle_error("loading template file {0}".format(self.template_path), e)
        except Exception as e:
            return handle_error("loading template file {0}".format(self.template_path), e)

    def add_component_data(self, component_name, parser):
        """
        Add component data from a parser.

        Args:
            component_name: Name of the component
            parser: ElfParser instance
        """
        self.component_data[component_name] = {
            'load_segments': parser.get_load_segments(),
            'meta_segments': parser.get_meta_segments(),
            'entry_point': parser.get_entry_point(),
            'arch': parser.get_architecture(),
            'os': image_os_mapping.get(component_name, "elf"),
            'type': image_type_mapping.get(component_name, "firmware")
        }

        # Also set component availability for conditional templates
        self.set_component_availability(component_name, True)

    def set_component_availability(self, component_name, available=True):
        """
        Set the availability of a component.

        Args:
            component_name: Name of the component
            available: Whether the component is available
        """
        define_name = 'HAVE_{0}'.format(component_name.upper())
        if define_name in self.component_defines:
            self.component_defines[define_name] = 1 if available else 0

    def set_placeholder(self, placeholder_name, value):
        """
        Set a placeholder value.

        Args:
            placeholder_name: Name of the placeholder
            value: Value to replace the placeholder with
        """
        self.placeholders[placeholder_name] = value

    def update_load_addresses(self):
        """
        Update the load addresses by setting placeholders for conditional templates.

        Returns:
            bool: True if the operation was successful, False otherwise
        """
        # For conditional templates, set placeholders instead
        for component_name, data in self.component_data.items():
            # Set entry point
            entry_point = data['entry_point']
            self.set_placeholder("{0}_ENTRY_ADDR".format(component_name.upper()), entry_point)

            # Set load addresses for each segment
            for i, segment in enumerate(data['load_segments'], 1):
                load_addr = segment["load_address"]
                self.set_placeholder("{0}_{1}_LOAD_ADDR".format(component_name.upper(), i), load_addr)
        return True

    def process_conditional_template(self):
        """
        Process the template by replacing #define directives and placeholders.

        Returns:
            bool: True if the operation was successful, False otherwise
        """
        if not self.template_content:
            print("Error: Template content not loaded")
            return False

        temp_path = None
        temp_file_added = False

        try:
            # Create a more secure temporary file name using PID and hash of template content
            # This reduces predictability while using only existing imports
            content_hash = hash(self.template_content) & 0x7FFFFFFF  # Ensure positive hash
            temp_path = "temp_template_{0}_{1}.its".format(os.getpid(), content_hash)
            abs_temp_path = os.path.join(os.getcwd(), temp_path)

            # Extract header content before /dts-v1/; directive
            header_content = ""
            processed_content = self.template_content

            # Find the /dts-v1/; directive
            dts_directive = "/dts-v1/;"
            dts_index = processed_content.find(dts_directive)

            if dts_index != -1:
                # Extract everything before and including /dts-v1/;
                dts_end = dts_index + len(dts_directive)
                header_content = processed_content[:dts_end]

                # Add a newline after the header if it doesn't already have one
                if not header_content.endswith('\n'):
                    header_content += '\n'

                # Process only the content after /dts-v1/;
                processed_content = processed_content[dts_end:].lstrip('\n')
            else:
                print("Warning: /dts-v1/; directive not found in template, processing entire content")

            # Replace #define values
            for define_name, define_value in self.component_defines.items():
                pattern = '#define {0} 0'.format(define_name)
                replacement = '#define {0} {1}'.format(define_name, define_value)
                processed_content = processed_content.replace(pattern, replacement)

            # Replace placeholders
            for placeholder_name, placeholder_value in self.placeholders.items():
                processed_content = processed_content.replace(placeholder_name, placeholder_value)

            # Write the processed content to the temporary file
            with open(temp_path, 'w') as temp_file:
                temp_file.write(processed_content)

            # Add this temporary file to the tracking list if available
            if hasattr(self, 'temp_files_list') and self.temp_files_list is not None and isinstance(self.temp_files_list, list):
                try:
                    self.temp_files_list.append(abs_temp_path)
                    temp_file_added = True
                except Exception as e:
                    print("Warning: Failed to add {0} to tracking list: {1}".format(abs_temp_path, e))
                    print("Note: Untracked temporary file created: {0}".format(abs_temp_path))

            # Use cpp to process the #if directives
            try:
                # Create a temporary file for the preprocessed output
                preprocessed_output_path = temp_path + ".preprocessed"

                # Use subprocess.call() instead of Popen
                returncode = subprocess.call(
                    ['cpp', '-P', '-nostdinc', '-undef', temp_path, '-o', preprocessed_output_path],
                    shell=False
                )

                if returncode != 0:
                    print("Error: cpp preprocessing failed with return code {0}".format(returncode))
                    raise RuntimeError("cpp preprocessing failed")

                # Read the preprocessed content
                with open(preprocessed_output_path, 'r') as preprocessed_file:
                    preprocessed_content = preprocessed_file.read()

                # Write the preprocessed content to the output file with header
                with open(self.output_path, 'w') as f:
                    # Write header content first if it exists
                    if header_content:
                        f.write(header_content)
                        f.write('\n')  # Add extra newline for separation

                    f.write(preprocessed_content)

                # Clean up the temporary preprocessed file
                if os.path.exists(preprocessed_output_path):
                    os.unlink(preprocessed_output_path)

                print("Generated ITS file: {0}".format(self.output_path))

                return True
            except (subprocess.SubprocessError, Exception) as e:
                handle_error("preprocessing template", e, False)
                raise  # Re-raise to be caught by outer try-except

        except (IOError, OSError, Exception) as e:
            return handle_error("processing template", e, False)
        finally:
            # Clean up the temporary file in all cases if it exists
            if temp_path:
                # Only attempt operations if the file exists
                if os.path.exists(temp_path):
                    try:
                        # First delete the file
                        os.unlink(temp_path)

                        # If deletion succeeds, remove from tracking list
                        if hasattr(self, 'temp_files_list') and self.temp_files_list is not None:
                            if abs_temp_path in self.temp_files_list:
                                self.temp_files_list.remove(abs_temp_path)
                    except Exception as e:
                        print("Warning: Failed to clean up temporary file {0}: {1}".format(temp_path, e))
                else:
                    # File doesn't exist but might be in tracking list
                    if hasattr(self, 'temp_files_list') and self.temp_files_list is not None:
                        if abs_temp_path in self.temp_files_list:
                            self.temp_files_list.remove(abs_temp_path)
                            print("Warning: Removed non-existent file {0} from tracking".format(temp_path))

    def save(self, output_path=None):
        """
        Save the modified template as the final ITS file.

        Args:
            output_path: Path to save the final ITS file (optional if already set in constructor)

        Returns:
            bool: True if the operation was successful, False otherwise
        """
        if output_path:
            self.output_path = output_path

        return self.process_conditional_template()

# Component mapping
path_to_component = {
    'qclib_path': 'qclib',
    'qcconfig_path': 'qcconfig',
    'tfa_bl31_path': 'tfa_bl31',
    'uboot_path': 'uboot',
    'optee_path': 'optee'
}

# OS mapping table
image_os_mapping = {
    "qclib": "elf",
    "qcconfig": "elf",
    "tfa_bl31": "arm-trusted-firmware",
    "uboot": "u-boot",
    "optee": "tee"
}

# Segment type mapping
image_type_mapping = {
    "uboot": "standalone",
    # All other components default to "firmware"
}

# Architecture mapping
arch_meta_load_addr = {
    "ipq5424": "0x8cf4800",
    "ipq5210": "0x08cb8000",
    "ipq9650": "0x08cf8000"
}

def handle_error(operation_name, e, default_return=False):
    """
    Common error handling function for operations.

    Args:
        operation_name: Name of the operation that failed
        e: Exception object
        default_return: Default value to return on error

    Returns:
        The default return value (usually False or empty list/dict)
    """
    error_type = "Error" if isinstance(e, (IOError, OSError)) else "Unexpected error"
    print("{0} in {1}: {2}".format(error_type, operation_name, e))
    return default_return

def validate_path(path):
    """
    Validate that a file path is safe and doesn't contain directory traversal attempts.

    Args:
        path: The file path to validate

    Returns:
        bool: True if the path is safe, False otherwise
    """
    try:
        if not path:
            return False  # Empty paths are considered invalid for security

        # Check for shell metacharacters that could be used for command injection
        if re.search(r'[;&|`$!*?~<>^()\[\]{}\'"]', path):
            return False

        # Check for absolute paths (both Unix and Windows styles)
        if os.path.isabs(path):
            return False

        # Check for potentially dangerous Unicode characters
        for char in path:
            if ord(char) > 127:  # Non-ASCII characters
                return False

        # Get the base directory for path resolution
        base_dir = os.path.abspath(os.getcwd())

        # Get the absolute path before normalization
        abs_path_before = os.path.abspath(os.path.join(base_dir, path))

        # Check if the path would resolve outside the base directory
        if not abs_path_before.startswith(base_dir):
            return False

        # Normalize the path once to handle all '..' and '.' components
        normalized_path = os.path.normpath(path)

        # Quick checks on the normalized path
        if not normalized_path or normalized_path == '.' or normalized_path == '..':
            return False

        if normalized_path.startswith('..'):
            return False

        # Check for directory traversal patterns in the normalized path
        path_parts = normalized_path.split(os.sep)
        if '..' in path_parts:
            return False

        # Handle Windows-style separators if on a non-Windows system
        if os.sep != '\\' and '\\' in normalized_path:
            win_path_parts = normalized_path.replace('\\', os.sep).split(os.sep)
            if '..' in win_path_parts:
                return False

        # Get the absolute path after normalization
        abs_path_after = os.path.abspath(os.path.join(base_dir, normalized_path))

        # Ensure the normalized path stays within the base directory
        if not abs_path_after.startswith(base_dir):
            return False

        # Additional check for paths that changed during normalization
        if abs_path_before != abs_path_after:
            rel_path = os.path.relpath(abs_path_after, base_dir)
            if rel_path.startswith('..'):
                return False

        # Validate each path component
        for component in path_parts:
            if component and not validate_filename(component):
                return False

        return True
    except (IOError, OSError, Exception) as e:
        return handle_error("validating path", e, False)

def validate_filename(filename):
    """
    Validate that a filename contains only safe characters.

    Args:
        filename: The filename to validate

    Returns:
        bool: True if the filename is safe, False otherwise
    """
    try:
        # Ensure filename doesn't start with a dot (hidden file)
        if filename.startswith('.'):
            return False
        # Ensure filename doesn't contain consecutive dots
        if '..' in filename:
            return False
        # Ensure filename doesn't contain any potentially dangerous characters
        # Use match with ^ and $ to ensure the entire string matches the pattern
        return bool(re.match(r'^[a-zA-Z0-9_\-\.]+$', filename))
    except (IOError, OSError, Exception) as e:
        return handle_error("validating filename", e, False)

def sanitize_path(path):
    """
    Sanitize a path to ensure it's safe for file operations.

    Args:
        path: The path to sanitize

    Returns:
        tuple: (bool, str) - (True, normalized_path) if valid, (False, None) if invalid
    """
    try:
        # First validate the path using the comprehensive validate_path function
        if not path or not validate_path(path):
            return (False, None)

        # Path is valid, return the normalized version
        return (True, os.path.normpath(path))
    except Exception as e:
        # Use the return value from handle_error for consistency
        success = handle_error("sanitizing path", e, False)
        return (success, None)

class ElfParser:
    """
    Class for parsing ELF/MBN files and extracting necessary information.
    """
    def __init__(self, input_file, component_name, output_dir, temp_files_list=None):
        """
        Initialize the ElfParser.

        Args:
            input_file: Path to the input ELF/MBN file
            component_name: Name of the component (used for output file naming)
            output_dir: Directory where output files will be saved
            temp_files_list: List to track temporary files created (optional)
        """
        self.input_file = input_file
        self.component_name = component_name
        self.load_segments = []
        self.meta_segments = []
        self.entry_point = None
        self.arch = None
        self.output_dir = output_dir
        self.temp_files_list = temp_files_list

    def parse(self):
        """
        Parse the ELF file and extract segments, entry point, and architecture.

        Returns:
            bool: True if the operation was successful, False otherwise
        """
        # Create output directory if it doesn't exist
        try:
            os.makedirs(self.output_dir)
        except OSError as e:
            if e.errno != errno.EEXIST:
                return handle_error("creating output directory", e)
        except Exception as e:
            return handle_error("creating output directory", e)

        load_info = []
        load_info_filename = os.path.join(self.output_dir, "{0}_load_addresses.txt".format(self.component_name))
        meta_filename = os.path.join(self.output_dir, "{0}_meta_segments.bin".format(self.component_name))

        # Track temporary files if a list was provided
        if self.temp_files_list is not None and isinstance(self.temp_files_list, list):
            try:
                self.temp_files_list.append(load_info_filename)
                self.temp_files_list.append(meta_filename)
            except Exception as e:
                print("Warning: Failed to add files to tracking list: {0}".format(e))
                print("Note: Untracked temporary files created: {0}, {1}".format(load_info_filename, meta_filename))

        # Use nested context managers to ensure proper cleanup of all resources
        try:
            # Open the ELF file in the outer context manager
            with mbn_tools.OPEN(self.input_file, "r+b") as elf:
                try:
                    # Open the meta file in an inner context manager
                    with open(meta_filename, "wb") as meta_bin_file:
                        [elf_header, phdr_table] = mbn_tools.preprocess_elf_file(self.input_file)

                        if elf_header.e_ident[mbn_tools.ELFINFO_CLASS_INDEX] == mbn_tools.ELFINFO_CLASS_64:
                            self.arch = "arm64"
                        else:
                            self.arch = "arm"

                        load_info.append("arch: {0}".format(self.arch))

                        null_segment_count = 1
                        load_segment_count = 1

                        # Process all segments
                        for phdr_index in range(elf_header.e_phnum):
                            curr_phdr = phdr_table[phdr_index]

                            # Read the data once
                            elf.seek(curr_phdr.p_offset)
                            data_len = curr_phdr.p_filesz
                            file_buff = elf.read(data_len)

                            # Handle NULL segments - write to meta file
                            if curr_phdr.p_type == 0x0 and (null_segment_count == 1 or null_segment_count == 2):
                                meta_bin_file.write(file_buff)

                                # Only add entry to load_info for the first NULL segment
                                if null_segment_count == 1:
                                    self.entry_point = elf_header.e_entry
                                    load_info.append("{0}_meta_segments.bin: 0x{1:X}".format(self.component_name, self.entry_point))

                                null_segment_count += 1

                            # Handle LOAD segments
                            if curr_phdr.p_type == 0x1 and curr_phdr.p_memsz > 0 and curr_phdr.p_filesz > 0:
                                load_filename = os.path.join(self.output_dir, "{0}_{1}_load_segment.bin".format(self.component_name, load_segment_count))

                                try:
                                    with open(load_filename, 'wb') as load_file:
                                        load_file.write(file_buff)
                                    # Track this temporary file if a list was provided
                                    if self.temp_files_list is not None and isinstance(self.temp_files_list, list):
                                        try:
                                            self.temp_files_list.append(load_filename)
                                        except Exception as e:
                                            print("Warning: Failed to add {0} to tracking list: {1}".format(load_filename, e))
                                            print("Note: Untracked temporary file created: {0}".format(load_filename))
                                except (IOError, OSError) as e:
                                    return handle_error("writing load segment file {0}".format(load_filename), e)
                                except Exception as e:
                                    return handle_error("writing load segment file {0}".format(load_filename), e)

                                load_address = curr_phdr.p_vaddr
                                segment_info = {
                                    'filename': os.path.basename(load_filename),
                                    'load_address': "0x{0:X}".format(load_address)
                                }
                                self.load_segments.append(segment_info)
                                load_info.append("{0}: 0x{1:X}".format(os.path.basename(load_filename), load_address))
                                load_segment_count += 1

                    # Write load info file in a separate context manager
                    try:
                        with open(load_info_filename, 'w') as info_file:
                            info_file.write("\n".join(load_info))
                    except (IOError, OSError) as e:
                        return handle_error("writing load info file {0}".format(load_info_filename), e)
                    except Exception as e:
                        return handle_error("writing load info file {0}".format(load_info_filename), e)

                    print("Splitted {0} into separate bins".format(self.component_name))
                    print("Saved load addresses to {0}_load_addresses.txt\n".format(self.component_name))

                except (IOError, OSError) as e:
                    return handle_error("processing meta file operations", e)
                except Exception as e:
                    return handle_error("processing meta file operations", e)

            # Add meta segment info
            self.meta_segments = [{
                'filename': "{0}_meta_segments.bin".format(self.component_name),
                'entry_point': "0x{0:X}".format(self.entry_point) if self.entry_point else "0x00000000"
            }]

            return True  # Success
        except (IOError, OSError) as e:
            return handle_error("opening ELF file", e)
        except Exception as e:
            return handle_error("opening ELF file", e)

    def get_load_segments(self):
        """
        Get the load segments.

        Returns:
            list: List of load segments
        """
        return self.load_segments

    def get_meta_segments(self):
        """
        Get the meta segments.

        Returns:
            list: List of meta segments
        """
        return self.meta_segments

    def get_entry_point(self):
        """
        Get the entry point.

        Returns:
            str: Entry point address as a hex string
        """
        return "0x{0:X}".format(self.entry_point) if self.entry_point else "0x00000000"

    def get_architecture(self):
        """
        Get the architecture.

        Returns:
            str: Architecture (arm or arm64)
        """
        return self.arch


class FitImageGenerator:
    """
    Class for orchestrating the FIT image generation process.
    """
    def __init__(self, args):
        """
        Initialize the FitImageGenerator.

        Args:
            args: Command line arguments
        """
        self.args = args
        self.template_manager = None
        self.parsers = {}
        self.temp_files = []  # List to track temporary files created during execution

        # Extract directory and filename from args.output
        output_dir, output_filename = os.path.split(args.output)
        if not output_dir:
            output_dir = os.getcwd()
        else:
            output_dir = os.path.join(os.getcwd(), output_dir)

        # Use the exact filename for .img file
        self.output_dir = output_dir
        self.img_file = os.path.join(self.output_dir, output_filename)

        # For .its file, remove extension if present and add .its
        filename_root, filename_ext = os.path.splitext(output_filename)
        if filename_ext:  # If there's an extension, remove it
            its_filename = "{0}.its".format(filename_root)
        else:  # If no extension, just add .its
            its_filename = "{0}.its".format(output_filename)

        self.its_file = os.path.join(self.output_dir, its_filename)

    def parse_input_files(self):
        """
        Parse the input ELF/MBN files.

        Returns:
            bool: True if the operation was successful, False otherwise
        """
        # Create output directory if it doesn't exist
        try:
            os.makedirs(self.output_dir)
        except OSError as e:
            if e.errno != errno.EEXIST:
                return handle_error("creating output directory", e)
        except Exception as e:
            return handle_error("creating output directory", e)

        # Parse each input file
        input_files = []
        for arg_name, file_path in [
            ('qclib_path', self.args.qclib_path),
            ('qcconfig_path', self.args.qcconfig_path),
            ('tfa_bl31_path', self.args.tfa_bl31_path),
            ('uboot_path', self.args.uboot_path),
            ('optee_path', self.args.optee_path)
        ]:
            if file_path:
                component_name = path_to_component[arg_name]
                input_files.append((file_path, component_name))

        # Parse each input file
        for file_path, component_name in input_files:
            parser = ElfParser(file_path, component_name, self.output_dir, self.temp_files)
            if not parser.parse():
                return False
            self.parsers[component_name] = parser

        # Handle DPR: copy the whole ELF to the output directory (no segment splitting)
        if self.args.dpr_path:
            dpr_basename = os.path.basename(self.args.dpr_path)
            output_dpr_path = os.path.join(self.output_dir, dpr_basename)
            try:
                shutil.copy2(self.args.dpr_path, output_dpr_path)
                self.temp_files.append(output_dpr_path)
                print("Copied DPR ELF to output directory: {0}".format(dpr_basename))
            except (IOError, OSError) as e:
                return handle_error("copying DPR ELF file", e, False)

        return True

    def generate_its_file(self):
        """
        Generate the ITS file from the template.

        Returns:
            bool: True if the operation was successful, False otherwise
        """
        # Create the template manager
        self.template_manager = TemplateManager(self.args.template, self.its_file, self.temp_files)
        if not self.template_manager.load_template():
            return False

        # Add component data to the template manager
        for component_name, parser in self.parsers.items():
            self.template_manager.add_component_data(component_name, parser)

        # Determine pre and post components
        pre_components = []
        post_components = []

        if self.args.pre is None and self.args.post is None:
            # Use default configuration
            default_pre = ['qcconfig', 'qclib']
            default_post = ['tfa_bl31', 'uboot', 'optee']

            pre_components = [comp for comp in default_pre if comp in self.parsers]
            post_components = [comp for comp in default_post if comp in self.parsers]

            print("Using default configuration:")
            print("Pre-DDR components: {0}".format(pre_components))
            print("Post-DDR components: {0}\n".format(post_components))
        else:
            # Use custom configuration
            if self.args.pre:
                pre_components = [comp for comp in self.args.pre if comp in self.parsers]
            if self.args.post:
                post_components = [comp for comp in self.args.post if comp in self.parsers]

        # Handle DTB file if provided
        if self.args.dtb_path:
            # Copy DTB file to output directory
            dtb_basename = os.path.basename(self.args.dtb_path)
            output_dtb_path = os.path.join(self.output_dir, dtb_basename)

            try:
                # Copy the DTB file to the output directory
                # shutil.copy2() will raise FileNotFoundError if source doesn't exist
                shutil.copy2(self.args.dtb_path, output_dtb_path)

                # Set FDT availability and placeholder
                self.template_manager.set_component_availability("FDT", True)
                self.template_manager.set_placeholder("FDT_PATH", dtb_basename)

                print("Copied DTB file to output directory: {0}".format(dtb_basename))

                # Don't track DTB file as temporary since it's a user-provided file
            except FileNotFoundError:
                print("Error: Source DTB file does not exist: {0}".format(self.args.dtb_path))
                return False
            except PermissionError:
                print("Error: Permission denied accessing DTB file: {0}".format(self.args.dtb_path))
                return False
            except (IOError, OSError) as e:
                return handle_error("copying DTB file", e, False)

        # Set meta load address placeholder with defensive programming
        meta_load_addr = arch_meta_load_addr.get(self.args.arch)
        if meta_load_addr is None:
            print("Error: Unsupported architecture '{0}'. Supported architectures: {1}".format(self.args.arch, list(arch_meta_load_addr.keys())))
            return False
        self.template_manager.set_placeholder("META_LOAD_ADDR", meta_load_addr)

        # Extract U-Boot architecture and set placeholder
        if 'uboot' in self.parsers:
            uboot_arch = self.parsers['uboot'].get_architecture()
            self.template_manager.set_placeholder("UBOOT_ARCH", uboot_arch)

        # Handle DPR if provided: enable the conditional block and set placeholders
        if self.args.dpr_path:
            dpr_basename = os.path.basename(self.args.dpr_path)
            self.template_manager.set_component_availability("DPR", True)
            self.template_manager.set_placeholder("DPR_FILENAME", dpr_basename)
            # Use the same load address as qcconfig segment 1
            if 'qcconfig' in self.parsers and self.parsers['qcconfig'].get_load_segments():
                dpr_load_addr = self.parsers['qcconfig'].get_load_segments()[0]['load_address']
                self.template_manager.set_placeholder("DPR_LOAD_ADDR", dpr_load_addr)
                print("DPR load address set to: {0} (same as qcconfig)".format(dpr_load_addr))
            else:
                print("Error: qcconfig load segments not available to derive DPR load address")
                return False

        # Update the template with load addresses and placeholders
        # Note: For conditional templates, only load address updates are needed.
        # Other operations (binary paths, entry addresses, OS type, configurations)
        # are handled during template processing via placeholders and #define directives.
        if not self.template_manager.update_load_addresses():
            return False

        # Save the modified template
        if not self.template_manager.save():
            return False

        return True

    def create_fit_image(self):
        """
        Create the FIT image using mkimage.

        Returns:
            bool: True if the operation was successful, False otherwise
        """
        try:
            # Use subprocess.call() instead of Popen
            returncode = subprocess.call(
                ['mkimage', '-E', '-f', os.path.basename(self.its_file), os.path.basename(self.img_file)],
                cwd=self.output_dir,
                shell=False  # Explicitly set shell=False to prevent command injection
            )

            # Check return code to determine if command was successful
            if returncode != 0:
                print("Error: mkimage command failed with return code {0}".format(returncode))
                return False
            else:
                print("Successfully created FIT image: {0}".format(self.img_file))
        except (subprocess.SubprocessError, Exception) as e:
            return handle_error("executing mkimage command", e, False)

        return True

    def cleanup_temporary_files(self):
        """
        Clean up temporary files created during the FIT image generation process.
        Only deletes files that were specifically created by this script execution.

        Returns:
            bool: True if the operation was successful, False otherwise
        """
        if not self.temp_files:
            print("No temporary files to clean up")
            return True

        for file_path in self.temp_files:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    print("Deleted temporary file: {0}".format(os.path.basename(file_path)))
                except (IOError, OSError, Exception) as e:
                    return handle_error("deleting temporary file {0}".format(file_path), e, False)

        return True

    def run(self):
        """
        Run the entire process.

        Returns:
            bool: True if the operation was successful, False otherwise
        """
        # Parse input files
        if not self.parse_input_files():
            return False

        # Generate ITS file
        if not self.generate_its_file():
            return False

        # Create FIT image
        if not self.create_fit_image():
            return False

        # Clean up temporary files
        if not self.cleanup_temporary_files():
            print("Warning: Failed to clean up some temporary files")

        return True

def main():
    """
    Main function that parses command line arguments and orchestrates the FIT image generation process.

    Returns:
        bool: True if the operation was successful, False otherwise
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Generate FIT image from ELF/MBN files with pre-DDR and post-DDR configurations using a template")
    parser.add_argument('--template', type=str, required=True,
                        help="Path to the template ITS file")
    parser.add_argument('--arch', type=str, choices=['ipq5424', 'ipq5210', 'ipq9650'],
                        required=True, help="Target architecture (ipq5424 or ipq5210 or ipq9650)")
    parser.add_argument('--qclib_path', type=str, required=True, help="Path to qclib ELF file")
    parser.add_argument('--qcconfig_path', type=str, required=True, help="Path to qcconfig ELF file")
    parser.add_argument('--tfa_bl31_path', type=str, required=True, help="Path to TFA BL31 MBN file")
    parser.add_argument('--uboot_path', type=str, required=True, help="Path to U-Boot MBN file")
    parser.add_argument('--optee_path', type=str, required=True, help="Path to OPTEE MBN file")
    parser.add_argument('-p', '--pre', nargs='+', default=None,
                        help="Files to include in pre-DDR configuration (optional, defaults to qclib qcconfig)")
    parser.add_argument('-P', '--post', nargs='+', default=None,
                        help="Files to include in post-DDR configuration (optional, defaults to tfa_bl31 uboot optee)")
    parser.add_argument('-o', '--output', type=str, required=True,
                        help="Output file path and name (e.g., './out_path/bootldr.img')")
    parser.add_argument('--dtb_path', type=str, help="Path to Device Tree Blob (DTB) file")
    parser.add_argument('--dpr', dest='dpr_path', type=str, default=None,
                        help="Path to DPR ELF file (optional). When provided, the entire ELF is "
                             "included as a single image in the FIT before qcconfig.")

    args = parser.parse_args()

    # Validate template path
    if not validate_path(args.template):
        print("Error: Invalid template path '{0}'. Path contains invalid characters or directory traversal attempts.".format(args.template))
        return False

    # Validate output path
    output_dir, output_file_base = os.path.split(args.output)

    # If output directory is specified, validate it
    if output_dir:
        success, normalized_path = sanitize_path(output_dir)
        if not success:
            print("Error: Invalid output directory path '{0}'. Path contains invalid characters or directory traversal attempts.".format(output_dir))
            return False

    # Validate output file base name if provided
    if output_file_base and not validate_filename(output_file_base):
        print("Error: Invalid output file base name '{0}'. Only alphanumeric characters, underscores, hyphens, and periods are allowed.".format(output_file_base))
        return False

    # Validate all input file paths
    for arg_name, file_path in [
        ('qclib_path', args.qclib_path),
        ('qcconfig_path', args.qcconfig_path),
        ('tfa_bl31_path', args.tfa_bl31_path),
        ('uboot_path', args.uboot_path),
        ('optee_path', args.optee_path),
        ('dtb_path', args.dtb_path),
        ('dpr_path', args.dpr_path)
    ]:
        if file_path:
            # Validate and sanitize the path
            success, normalized_path = sanitize_path(file_path)
            if not success:
                print("Error: Invalid file path '{0}' for {1}. Path contains invalid characters or directory traversal attempts.".format(file_path, arg_name))
                return False

            # Update the argument with the normalized path
            setattr(args, arg_name, normalized_path)

    # Initialize and run the FIT image generator
    generator = FitImageGenerator(args)
    return generator.run()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
