#!/usr/bin/env python3
"""
KML Layer Splitter

This script processes a KML file containing multiple layers (folders) and
creates individual KML files for each layer while preserving all layer information.

Usage:
    python kml_splitter.py input.kml [--debug] [--force]

Options:
    --debug     Show detailed diagnostic information about the KML file
    --force     Attempt to repair malformed KML files

Output:
    Creates individual KML files named after each layer in the input file
"""

import sys
import os
import re
import argparse
from lxml import etree
import xml.etree.ElementTree as ET  # For fallback parsing

# Define common KML namespaces
NAMESPACES = {
    'kml': 'http://www.opengis.net/kml/2.2',
    'gx': 'http://www.google.com/kml/ext/2.2',
    'atom': 'http://www.w3.org/2005/Atom',
    'xal': 'urn:oasis:names:tc:ciq:xsdschema:xAL:2.0'
}

def sanitize_filename(name):
    """Convert a layer name to a valid filename."""
    # Remove invalid filename characters
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    # Replace spaces with underscores
    name = name.replace(' ', '_')
    # Make sure it's not empty
    if not name:
        name = "unnamed_layer"
    return name

def create_base_kml():
    """Create a new KML document with necessary structure."""
    root = etree.Element("{http://www.opengis.net/kml/2.2}kml")
    doc = etree.SubElement(root, "{http://www.opengis.net/kml/2.2}Document")
    return root, doc

def copy_styles(source_doc, target_doc):
    """Copy all style definitions from source to target document."""
    # Find all Style and StyleMap elements
    styles = source_doc.findall('.//kml:Style', namespaces=NAMESPACES)
    styles.extend(source_doc.findall('.//kml:StyleMap', namespaces=NAMESPACES))
    
    if not styles:
        # Try without namespace if no styles found
        styles = source_doc.findall('.//Style')
        styles.extend(source_doc.findall('.//StyleMap'))
    
    # Copy each style to the target document
    for style in styles:
        try:
            target_doc.append(etree.fromstring(etree.tostring(style)))
        except Exception as e:
            print(f"Warning: Could not copy style: {e}")

def save_kml_file(root, filename):
    """Save KML tree to a file with proper formatting."""
    tree = etree.ElementTree(root)
    
    # Ensure the filename has .kml extension
    if not filename.lower().endswith('.kml'):
        filename += '.kml'
    
    # Pretty print with proper XML declaration
    tree.write(filename, pretty_print=True, 
              xml_declaration=True, encoding='UTF-8')
    
    return filename

def detect_namespaces(xml_content):
    """Detect XML namespaces in the content."""
    custom_namespaces = {}
    
    # Look for namespace declarations in the XML
    ns_matches = re.findall(r'xmlns:(\w+)="([^"]+)"', xml_content)
    for prefix, uri in ns_matches:
        custom_namespaces[prefix] = uri
    
    # Add the default namespace if present
    default_ns_match = re.search(r'xmlns="([^"]+)"', xml_content)
    if default_ns_match:
        custom_namespaces['default'] = default_ns_match.group(1)
    
    return custom_namespaces

def diagnose_kml(file_path):
    """Provide diagnostic information about the KML file."""
    print("\n--- KML File Diagnostics ---")
    
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
            
        # Check for XML declaration
        if not content.startswith(b'<?xml'):
            print("Warning: File does not start with XML declaration")
        
        # Convert to string for regex
        content_str = content.decode('utf-8', errors='replace')
        
        # Check for KML namespace
        if 'http://www.opengis.net/kml/2.2' not in content_str:
            print("Warning: Standard KML namespace not found")
        
        # Detect all namespaces
        namespaces = detect_namespaces(content_str)
        print(f"Detected namespaces: {namespaces}")
        
        # Check root element
        root_match = re.search(r'<(\w+:?\w*)[^>]*>', content_str)
        if root_match:
            root_element = root_match.group(1)
            print(f"Root element: {root_element}")
            if root_element != 'kml' and not root_element.endswith(':kml'):
                print(f"Warning: Root element is not 'kml' but '{root_element}'")
        else:
            print("Error: Could not identify root element")
        
        # Check encoding
        encoding_match = re.search(r'encoding=["\']([^"\']+)["\']', content_str[:1000])
        if encoding_match:
            print(f"Encoding: {encoding_match.group(1)}")
        else:
            print("No encoding specified in XML declaration")
        
        # Try to parse with different parsers
        try:
            etree.fromstring(content)
            print("✓ lxml parser: File can be parsed")
        except Exception as e:
            print(f"✗ lxml parser error: {e}")
        
        try:
            ET.fromstring(content_str)
            print("✓ ElementTree parser: File can be parsed")
        except Exception as e:
            print(f"✗ ElementTree parser error: {e}")
            
    except Exception as e:
        print(f"Error during diagnostics: {e}")
    
    print("--- End of Diagnostics ---\n")

def attempt_repair(file_path):
    """Attempt to repair common KML formatting issues."""
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
        
        content_str = content.decode('utf-8', errors='replace')
        
        # 1. Ensure XML declaration exists
        if not content_str.startswith('<?xml'):
            content_str = '<?xml version="1.0" encoding="UTF-8"?>\n' + content_str
        
        # 2. Check for KML namespace in root element
        if '<kml' in content_str and 'xmlns' not in content_str[:content_str.find('>')+1]:
            content_str = content_str.replace('<kml', '<kml xmlns="http://www.opengis.net/kml/2.2"', 1)
        
        # 3. Ensure root element is kml if missing
        if not re.search(r'<\w*:?kml[^>]*>', content_str):
            if '<Document' in content_str:
                content_str = content_str.replace('<Document', '<kml xmlns="http://www.opengis.net/kml/2.2"><Document', 1)
                content_str += '</kml>'
        
        # 4. Fix common XML issues
        content_str = re.sub(r'&(?!amp;|lt;|gt;|quot;|apos;)', '&amp;', content_str)
        
        # Write repaired content to a temporary file
        temp_file = file_path + '.repaired.kml'
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(content_str)
        
        print(f"Attempted to repair KML file. Repaired version saved as {temp_file}")
        return temp_file
        
    except Exception as e:
        print(f"Error during repair attempt: {e}")
        return file_path

def process_kml_file(input_file, debug=False):
    """Process a KML file and split it by folders (layers) or individual elements."""
    try:
        # First try with lxml's parser
        parser = etree.XMLParser(recover=True, remove_blank_text=True, resolve_entities=False)
        tree = etree.parse(input_file, parser)
        root = tree.getroot()

        # Check if we have the right root
        root_tag = etree.QName(root).localname
        if root_tag != 'kml':
            print(f"Warning: Root element is '{root_tag}', not 'kml'. Attempting to process anyway.")

        # Try to find Document, with or without namespace
        doc = root.find('.//kml:Document', namespaces=NAMESPACES)
        if doc is None:
            doc = root.find('.//Document')

        # If we still can't find Document, maybe the root is already a Document
        if doc is None and etree.QName(root).localname == 'Document':
            doc = root

        if doc is None:
            raise ValueError("No Document element found in the KML file")

        # Get document name if available
        doc_name = None
        name_elem = doc.find('.//kml:name', namespaces=NAMESPACES)
        if name_elem is None:
            name_elem = doc.find('.//name')

        if name_elem is not None and name_elem.text:
            doc_name = name_elem.text
        else:
            doc_name = os.path.basename(input_file)

        # Find all folders, with or without namespace
        folders = doc.findall('.//kml:Folder', namespaces=NAMESPACES)
        if not folders:
            folders = doc.findall('.//Folder')

        if not folders:
            print(f"No folders/layers found in {input_file}")
            print("Looking for individual elements directly in the Document...")

            # If no folders, process all child elements of the Document
            elements = doc.findall('./*', namespaces=NAMESPACES)

            if not elements:
                print("No elements found either. Nothing to process.")
                return

            print(f"Found {len(elements)} elements in {input_file}")

            # Process each element
            for i, element in enumerate(elements):
                # Get element tag name (e.g., Placemark, Folder, GroundOverlay)
                tag_name = etree.QName(element.tag).localname

                # Generate a unique name for the layer
                element_name = element.findtext('kml:name', namespaces=NAMESPACES) or f"{tag_name}_{i+1}"
                print(f"Processing element: {element_name} (Tag: {tag_name})")

                # Create a new KML document for this element
                new_root, new_doc = create_base_kml()

                # Set document name (use the sublayer name)
                doc_name_elem = etree.SubElement(new_doc, "{http://www.opengis.net/kml/2.2}name")
                doc_name_elem.text = element_name  # Use the sublayer name

                # Copy styles from original document
                copy_styles(doc, new_doc)

                # Copy this element to the new document
                new_element = etree.fromstring(etree.tostring(element))
                new_doc.append(new_element)

                # Copy additional metadata (e.g., description, extended data)
                for metadata_tag in ['description', 'Snippet', 'ExtendedData']:
                    metadata_elem = element.find(f'kml:{metadata_tag}', namespaces=NAMESPACES)
                    if metadata_elem is not None:
                        new_metadata_elem = etree.fromstring(etree.tostring(metadata_elem))
                        new_doc.append(new_metadata_elem)

                # Save to a new file
                safe_name = sanitize_filename(element_name)
                # Save KML file relative to the script's location
                script_dir = os.path.dirname(os.path.abspath(__file__))
                output_file = os.path.join(script_dir, f"{safe_name}.kml")
                save_kml_file(new_root, output_file)
                print(f"Created: {output_file}")

            print("All elements have been successfully extracted to individual KML files.")
            return

        print(f"Found {len(folders)} layers in {input_file}")

        # Process each folder
        for folder in folders:
            # Get folder name
            folder_name = None
            name_elem = folder.find('./kml:name', namespaces=NAMESPACES)
            if name_elem is None:
                name_elem = folder.find('./name')

            if name_elem is not None and name_elem.text:
                folder_name = name_elem.text
            else:
                folder_name = f"unnamed_layer_{folders.index(folder)}"

            print(f"Processing layer: {folder_name}")

            # Create a new KML document for this folder
            new_root, new_doc = create_base_kml()

            # Set document name
            doc_name_elem = etree.SubElement(new_doc, "{http://www.opengis.net/kml/2.2}name")
            doc_name_elem.text = f"{doc_name} - {folder_name}"

            # Copy styles from original document
            copy_styles(doc, new_doc)

            # Copy this folder to the new document
            try:
                new_folder = etree.fromstring(etree.tostring(folder))
                new_doc.append(new_folder)

                # Save to a new file
                safe_name = sanitize_filename(folder_name)
                # Save KML file relative to the script's location
                script_dir = os.path.dirname(os.path.abspath(__file__))
                output_file = os.path.join(script_dir, f"{safe_name}.kml")
                save_kml_file(new_root, output_file)
                print(f"Created: {output_file}")
            except Exception as e:
                print(f"Error processing folder '{folder_name}': {e}")

        print("All layers have been successfully extracted to individual KML files.")

    except Exception as e:
        print(f"Error processing KML file: {e}")
        if debug:
            import traceback
            traceback.print_exc()

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description='Split a KML file into separate files by layer')
    parser.add_argument('input_file', help='KML file to process')
    parser.add_argument('--debug', action='store_true', help='Show detailed diagnostic information')
    parser.add_argument('--force', action='store_true', help='Attempt to repair malformed KML files')
    args = parser.parse_args()
    
    if not os.path.exists(args.input_file):
        print(f"Error: File '{args.input_file}' not found.")
        sys.exit(1)
    
    if not args.input_file.lower().endswith('.kml'):
        print("Warning: Input file does not have .kml extension.")
    
    print(f"Processing: {args.input_file}")
    
    # Run diagnostics if requested
    if args.debug:
        diagnose_kml(args.input_file)
    
    # Try to repair the file if requested
    input_file = args.input_file
    if args.force:
        input_file = attempt_repair(args.input_file)
    
    # Process the KML file
    process_kml_file(input_file, args.debug)

if __name__ == "__main__":
    main()
