# CoT Converter Project

TAK and ATAK both utilize Cursor on Target (CoT) XML format for sharing information. This project provides tools to convert KML files into CoT XML format, making it easier to integrate geographic data into these systems. While ATAK supports KML files, converting them to CoT XML format allows for better compatibility and functionality within the TAK ecosystem.

The tool is designed to process KML files and convert them into Cursor on Target (CoT) XML format for use in ATAK (Android Team Awareness Kit). 

The scripts are:

1. **main.py**: The main entry point for converting KML files into CoT XML format, handling points, lines, and polygons while preserving metadata.
2. **kml_splitter.py**: Splits large KML files into smaller, more manageable KML files.
3. **kmz_to_kml.py**: Converts KMZ files to KML format, allowing for easier processing of compressed KML files
4. **data_package_gen.py**: TAK only accepts CoT files when they are in a data package format. This script generates a data package from CoT XML files, making them ready for use in TAK. It puts each CoT file into a separate directory and creates a manifest file for the data package.


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
python main.py key_points.kml --output ./output --prefix Key_Points --debug
```
This command converts `key_points.kml` into CoT XML files, saves them in the `./output` directory, and uses `Key_Points` as the filename prefix. Debugging information will be displayed during the process.

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
## Data Package Generation
The `data_package_gen.py` script generates a TAK data package from CoT XML files. It organizes each CoT file into a separate directory and creates a manifest file for the data package.
#### Command-Line Options
- `input_dir`: Directory containing CoT XML files to package.
- `--output OUTPUT_DIR`: Directory to save the generated data package (default: `./data_package`).
#### Example Usage
```bash
python data_package_gen.py ./cot_files --output ./data_package
```
This command generates a TAK data package from CoT XML files in the `./cot_files` directory and saves it in the `./data_package` directory.
## KMZ to KML Conversion
The `kmz_to_kml.py` script converts KMZ files to KML format, allowing for easier processing of compressed KML files.
#### Command-Line Options
- `input.kmz`: The input KMZ file to convert.
- `--output OUTPUT_DIR`: Directory to save the converted KML files (default: `./kmz_converted`).
#### Example Usage
```bash
python kmz_to_kml.py input.kmz --output ./kmz_converted
```
This command converts `input.kmz` into KML format and saves it in the `./kmz_converted` directory.
## Requirements
To run the scripts, you need Python 3.x and the following libraries:
- `xml.etree.ElementTree`
- `os`
- `shutil`
- `argparse`
- `zipfile`
- `re`
- `lxml` (for XML parsing and manipulation)
- `geopy` (for geographic calculations, if needed)

You can install the required libraries using using poetry:

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing
Contributions are welcome! If you find a bug or have a feature request, please open an issue. Pull requests are also welcome. Please ensure that your code adheres to the project's coding standards and includes appropriate tests.