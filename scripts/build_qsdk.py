# ===========================================================================
# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: ISC
# ===========================================================================

import subprocess
import argparse
import sys
import os

def sync_repo(folder_name, au_tag):
	try:
		setup_and_sync = f"""
		set -e
		mkdir -p {folder_name} && \\
		cd {folder_name} && umask 022 &&\\
		repo init --depth=1 --current-branch \\
		-u https://git.codelinaro.org/clo/qsdk/releases/manifest/qstak.git \\
		-b release -m {au_tag}.xml \\
		--repo-url=https://git.codelinaro.org/clo/tools/repo.git \\
		--repo-branch=qc-stable && \\
		repo sync -j8
		"""
		subprocess.run(setup_and_sync, shell=True, check=True, executable="/bin/bash")
		return True
	except subprocess.CalledProcessError as e:
		print(f"\nRepo sync failed:\n{e}")
		return False

def modify_qsdk_file(file_path):
	append_string = ' -kmod-qca-nss-eip -kmod-qca-nss-eip-crypto -kmod-qca-nss-eip-ipsec'
	with open(file_path, 'r') as file:
		lines = file.readlines()

	modified = False
	in_target_section = False

	for i in range(len(lines)):
		line = lines[i]
		if line.strip().startswith('define Profile/QSDK_Open ') or line.strip() == 'define Profile/QSDK_Open':
			in_target_section = True
			continue

		if in_target_section and lines[i].strip().startswith('define Profile/'):
			break  # Exit if another profile starts

		if in_target_section and '$(NSS_CRYPTO)' in lines[i]:
			if append_string not in lines[i]:
				parts = line.split('$(NSS_CRYPTO)')
				lines[i] = parts[0] + '$(NSS_CRYPTO)' + append_string + parts[1]
				modified = True
				print(f"Found line with $(NSS_CRYPTO) at line {i}: {line.strip()}")
			break

	if modified:
		with open(file_path, 'w') as file:
			file.writelines(lines)
		print("File updated successfully.")
	else:
		print("No changes made. Either the section or the target line was not found.")

def build_qsdk(folder_name, target, arch, profile):
	try:
		build_commands = f"""
		cd {folder_name}/qsdk && \\
		source qca/configs/qsdk/setup-environment \\
		-t {target} -a {arch} -p {profile} -d n -c n -e false && \\
		make V=s -j8
		"""
		subprocess.run(build_commands, shell=True, check=True, executable="/bin/bash")
		return True
	except subprocess.CalledProcessError as e:
		print(f"\nBuild failed:\n{e}")
		return False

def main():
	soc_options = ["ipq95xx", "ipq53xx", "ipq54xx"]
	arch_options = ["32", "64"]

	parser = argparse.ArgumentParser(description="Build QSDK")
	parser.add_argument("-t", "--target", choices=soc_options, help="Target SoC")
	parser.add_argument("-a", "--arch", choices=arch_options, help="Architecture")
	parser.add_argument("-g", "--get", nargs=2, metavar=('AU_TAG', 'QART_VERSION'),
						help="AU tag and Qart version string")
	parser.add_argument("-w", "--workspace", help="Workspace name")
	parser.add_argument("-b", "--build", action='store_true', help="Build QSDK")
	parser.add_argument("-p", "--pack", action='store_true', help="Generate Single image")
	parser.add_argument("-i", "--install", action='store_true', help="Copy the built artifacts to install folder")

	args = parser.parse_args()

	if args.target and args.arch:
		target = args.target
		arch = args.arch
		profile = "open"
		folder_name = os.path.basename(args.workspace) if args.workspace else f"{target}_{arch}_{profile}"

		if args.get:
			au_tag, version_string = args.get
			if not sync_repo(folder_name, au_tag):
				sys.exit(1)
			if target == "ipq95xx":
				qsdk_mk_path = os.path.join(folder_name, "qsdk", "target", "linux", "feeds", "profiles", "qsdk.mk")
				modify_qsdk_file(qsdk_mk_path)
		else:
			version_string = "unknown"

		if args.build:
			if not build_qsdk(folder_name, target, arch, profile):
				sys.exit(1)

		script_path = os.path.join(folder_name, "meta-tools-oss", "scripts")

		if args.get:
			print(f"\nRunning prepare_bin.py for {target}...")
			subprocess.run(["python", "prepare_bin.py", target, version_string], check=True, cwd=script_path)

		if args.install or (args.build and args.pack):
			print(f"\nRunning copy_bin.py for {target} {arch}-bit...")
			subprocess.run(["python", "copy_bin.py", target, arch], check=True, cwd=script_path)

		if args.pack:
			print(f"\nRunning gen_single_image.py for {target} {arch}-bit...")
			subprocess.run(["python", "gen_single_image.py", target, arch], check=True, cwd=script_path)

	else:
		print("Target and architecture must be specified.")
		sys.exit(1)

if __name__ == "__main__":
	main()
