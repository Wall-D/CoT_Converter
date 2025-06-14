import sys
import os
import argparse

from CoT_Converter.kml_parser import diagnose_kml, attempt_repair, parse_kml_file
from CoT_Converter.cot_generator import process_placemarks
from CoT_Converter.utils import sanitize_filename

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description='Convert KML to CoT format for ATAK')
    parser.add_argument('input_file', help='KML file to convert')
    parser.add_argument('--prefix', dest='prefix', default=None,
                        help='Prefix for output filenames (default: based on input filename)')
    parser.add_argument('--output', dest='output_dir', default=None,
                        help='Directory to save output files (default: ./converted_files)')
    parser.add_argument('--debug', action='store_true', help='Show detailed diagnostic information')
    parser.add_argument('--force', action='store_true', help='Attempt to repair malformed KML files')
    args = parser.parse_args()
    
    # Check if the input file exists
    if not os.path.exists(args.input_file):
        print(f"Error: File '{args.input_file}' not found.")
        sys.exit(1)
    
    # Generate prefix from filename if not provided
    if not args.prefix:
        args.prefix = sanitize_filename(os.path.splitext(os.path.basename(args.input_file))[0])
    
    # Use provided output directory or default to "converted_files" in the current directory
    output_dir = args.output_dir or os.path.join(os.getcwd(), "converted_files")
    os.makedirs(output_dir, exist_ok=True)

    print(f"Processing: {args.input_file}")
    print(f"Output directory: {output_dir}")
    print(f"Prefix: {args.prefix}")

    # Check if the output directory is writable
    if not os.access(output_dir, os.W_OK):
        print(f"Error: Output directory '{output_dir}' is not writable.")
        sys.exit(1)

    # Run diagnostics if requested
    if args.debug:
        diagnose_kml(args.input_file)
    
    # Try to repair the file if requested
    input_file = args.input_file
    if args.force:
        input_file = attempt_repair(args.input_file)

    # Parse the KML file and process placemarks
    try:
        placemarks, root = parse_kml_file(input_file, args.debug)
        process_placemarks(placemarks, output_dir, args.prefix, args.debug)
    except Exception as e:
        print(f"Error: Failed to process KML file: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()