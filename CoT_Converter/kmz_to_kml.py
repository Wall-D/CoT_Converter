import os
import zipfile
import argparse
from datetime import datetime

def extract_kmz(kmz_file, output_dir):
    """Extract .kmz file into individual .kml files while preserving metadata."""
    if not os.path.exists(kmz_file):
        print(f"Error: File '{kmz_file}' does not exist.")
        return

    if not kmz_file.endswith(".kmz"):
        print(f"Error: File '{kmz_file}' is not a .kmz file.")
        return

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    try:
        with zipfile.ZipFile(kmz_file, 'r') as kmz:
            # Extract all files
            kmz.extractall(output_dir)
            print(f"Extracted '{kmz_file}' into '{output_dir}'")

            # Rename .kml files to include metadata
            for file_name in os.listdir(output_dir):
                if file_name.endswith(".kml"):
                    original_path = os.path.join(output_dir, file_name)
                    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                    new_name = f"{os.path.splitext(file_name)[0]}_{timestamp}.kml"
                    new_path = os.path.join(output_dir, new_name)
                    os.rename(original_path, new_path)
                    print(f"Renamed '{file_name}' to '{new_name}'")
    except zipfile.BadZipFile:
        print(f"Error: File '{kmz_file}' is not a valid .kmz file.")
    except Exception as e:
        print(f"Error: Failed to extract '{kmz_file}': {e}")

def main():
    parser = argparse.ArgumentParser(description="Unzip a .kmz file into individual .kml files while preserving metadata.")
    parser.add_argument("kmz_file", help="Path to the .kmz file to extract")
    parser.add_argument("--output", default="./extracted_kmls", help="Directory to save extracted .kml files (default: ./extracted_kmls)")
    args = parser.parse_args()

    extract_kmz(args.kmz_file, args.output)

if __name__ == "__main__":
    main()