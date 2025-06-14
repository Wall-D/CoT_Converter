import os
import shutil
import zipfile
import argparse
from datetime import datetime

def create_directories(base_dir):
    """Create 'MANIFEST' directory."""
    manifest_dir = os.path.join(base_dir, "MANIFEST")
    os.makedirs(manifest_dir, exist_ok=True)
    return manifest_dir

def extract_call_sign(file_path):
    """Extract the call sign from the .cot file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if "<contact callsign=" in line:
                    start = line.find('callsign="') + len('callsign="')
                    end = line.find('"', start)
                    return line[start:end]
    except Exception as e:
        print(f"Warning: Failed to extract call sign from {file_path}: {e}")
    return "Unknown"

def move_files_to_uid_folders(source_dir, base_dir):
    """Move files from 'converted_files' to individual UID folders."""
    file_data = []  # List of tuples (UID, call_sign)
    for file in os.listdir(source_dir):
        if file.endswith(".cot"):
            uid = os.path.splitext(file)[0]  # Extract UID from file name
            call_sign = extract_call_sign(os.path.join(source_dir, file))  # Extract call sign
            uid_folder = os.path.join(base_dir, uid)  # Create folder for UID
            os.makedirs(uid_folder, exist_ok=True)
            destination = os.path.join(uid_folder, file)  # Place file in UID folder
            shutil.copy(os.path.join(source_dir, file), destination)
            file_data.append((uid, call_sign))
    return file_data

def create_manifest(file_data, manifest_dir, package_name):
    """Create manifest.xml file based on the UID folders."""
    manifest_path = os.path.join(manifest_dir, "manifest.xml")
    with open(manifest_path, "w", encoding="utf-8") as manifest_file:
        manifest_file.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        manifest_file.write('<MissionPackageManifest version="2">\n')
        manifest_file.write('   <Configuration>\n')
        manifest_file.write(f'      <Parameter name="name" value="{package_name}"/>\n')  # Use package name
        manifest_file.write(f'      <Parameter name="uid" value="{datetime.now().strftime("%Y%m%d%H%M%S")}"/>\n')
        manifest_file.write('   </Configuration>\n')
        manifest_file.write('   <Contents>\n')
        for uid, call_sign in file_data:
            manifest_file.write(f'      <Content ignore="false" zipEntry="{uid}/{uid}.cot">\n')
            manifest_file.write(f'         <Parameter name="uid" value="{uid}"/>\n')
            manifest_file.write(f'         <Parameter name="name" value="{call_sign}"/>\n')
            manifest_file.write('      </Content>\n')
        manifest_file.write('   </Contents>\n')
        manifest_file.write('</MissionPackageManifest>\n')
    print(f"Manifest created at: {manifest_path}")
    return manifest_path

def zip_directories(base_dir, package_name, file_data):
    """Zip UID folders and 'MANIFEST' directory into a single package."""
    zip_path = os.path.join(base_dir, f"{package_name}.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(base_dir):
            for file in files:
                # Include UID folders and MANIFEST directory in the zip file
                if "MANIFEST" in root or os.path.basename(root) in [uid for uid, _ in file_data]:
                    zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), base_dir))
    print(f"Data package created: {zip_path}")
    return zip_path

def main():
    parser = argparse.ArgumentParser(description="Generate a data package from converted CoT files.")
    parser.add_argument("package_name", help="Name of the data package (without extension)")
    parser.add_argument("--source", default="./converted_files", help="Source directory containing CoT files (default: ./converted_files)")
    parser.add_argument("--output", default="./", help="Output directory for the data package (default: current directory)")
    args = parser.parse_args()

    # Create MANIFEST directory
    manifest_dir = create_directories(args.output)

    # Move files to individual UID folders
    file_data = move_files_to_uid_folders(args.source, args.output)

    # Create manifest.xml
    create_manifest(file_data, manifest_dir, args.package_name)  # Pass package name

    # Zip directories
    zip_directories(args.output, args.package_name, file_data)

if __name__ == "__main__":
    main()