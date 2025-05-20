# CoT Converter Project

This repository contains two Python scripts designed to process KML files and convert them into Cursor on Target (CoT) XML format for use in ATAK (Android Team Awareness Kit). The scripts are:

1. **kml_to_cot.py**: Converts KML files into CoT XML format, handling points, lines, and polygons while preserving metadata.
2. **kml_splitter.py**: Splits large KML files into smaller, more manageable KML files.

## Usage

### kml_to_cot.py
This script processes KML files and converts placemarks into CoT XML format. It supports points, lines, and polygons and includes options for debugging and repairing malformed KML files.

#### Command-Line Options
- `input.kml`: The input KML file to convert.
- `--output OUTPUT_DIR`: Directory to save output files (default: current directory).
- `--prefix PREFIX`: Prefix for output filenames (default: based on input filename).
- `--debug`: Show detailed diagnostic information.
- `--force`: Attempt to repair malformed KML files.

#### Example Usage
```bash
python kml_to_cot.py input.kml --output ./output --prefix my_prefix --debug
```
This command converts `input.kml` into CoT XML files, saves them in the `./output` directory, and uses `my_prefix` as the filename prefix. Debugging information will be displayed during the process.

### kml_splitter.py
This script splits large KML files into smaller KML files, making them easier to manage and process.

#### Command-Line Options
- `input.kml`: The input KML file to split.
- `--output OUTPUT_DIR`: Directory to save the split KML files (default: current directory).
- `--size SIZE`: Maximum number of placemarks per split file (default: 100).

#### Example Usage
```bash
python kml_splitter.py input.kml --output ./split_files --size 50
```
This command splits `input.kml` into smaller KML files, each containing up to 50 placemarks, and saves them in the `./split_files` directory.

## License
This project is licensed under the MIT License. See the `LICENSE` file for details.