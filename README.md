# CoT Converter Project

This repository contains Python scripts designed to process KML files and convert them into Cursor on Target (CoT) XML format for use in ATAK (Android Team Awareness Kit). The scripts are:

1. **main.py**: The main entry point for converting KML files into CoT XML format, handling points, lines, and polygons while preserving metadata.
2. **kml_splitter.py**: Splits large KML files into smaller, more manageable KML files.

## Usage

### main.py
This script processes KML files and converts placemarks into CoT XML format. It supports points, lines, and polygons and includes options for debugging and repairing malformed KML files. It can process a single KML file or an entire folder of `.kml` files.

#### Command-Line Options
- `input_file`: The input KML file or folder containing `.kml` files to convert.
- `--output OUTPUT_DIR`: Directory to save output files (default: `./converted_files`).
- `--prefix PREFIX`: Prefix for output filenames (default: based on input filename).
- `--debug`: Show detailed diagnostic information.
- `--force`: Attempt to repair malformed KML files.

#### Example Usage
To process a single KML file:
```bash
python main.py Town.kml --output ./output --prefix town --debug
```
This command converts `Town.kml` into CoT XML files, saves them in the `./output` directory, and uses `town` as the filename prefix. Debugging information will be displayed during the process.

To process a folder of KML files:
```bash
python main.py ./kml_folder --output ./output_folder --debug
```
This command processes all `.kml` files in the `./kml_folder` directory, converts them into CoT XML files, and saves them in the `./output_folder` directory. Debugging information will be displayed during the process.

---

### kml_splitter.py
This script splits large KML files into smaller KML files, making them easier to manage and process.

#### Command-Line Options
- `input.kml`: The input KML file to split.
- `--output OUTPUT_DIR`: Directory to save the split KML files (default: `./split_files`).
- `--size SIZE`: Maximum number of placemarks per split file (default: 100).

#### Example Usage
```bash
python kml_splitter.py input.kml --output ./split_files --size 50
```
This command splits `input.kml` into smaller KML files, each containing up to 50 placemarks, and saves them in the `./split_files` directory.

---

## Processing a Folder of KML Files
Both scripts support processing an entire folder of `.kml` files. Simply provide the folder path as the input, and the script will process all `.kml` files in that folder.

For example:
```bash
python main.py ./kml_folder --output ./output_folder --debug
```
This processes all `.kml` files in the `./kml_folder` directory and saves the converted CoT XML files in the `./output_folder` directory.

---

## License
This project is licensed under the MIT License. See the `LICENSE` file for details.