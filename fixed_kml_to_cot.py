def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description='Convert KML to CoT format for ATAK')
    parser.add_argument('input_file', help='KML file to convert')
    parser.add_argument('--output', dest='output_dir', default=None,
                        help='Directory to save output files (default: based on input filename + "_output")')
    parser.add_argument('--prefix', dest='prefix', default=None,
                        help='Prefix for output filenames (default: based on input filename)')
    parser.add_argument('--debug', action='store_true', help='Show detailed diagnostic information')
    parser.add_argument('--force', action='store_true', help='Attempt to repair malformed KML files')
    args = parser.parse_args()
    
    # Check if the input file exists
    if not os.path.exists(args.input_file):
        print(f"Error: File '{args.input_file}' not found.")
        sys.exit(1)
    
    # Generate prefix from filename if not provided
    if not args.prefix:
        # Use basename without extension
        args.prefix = os.path.splitext(os.path.basename(args.input_file))[0]
    
    # Generate default output directory if not provided
    if not args.output_dir:
        args.output_dir = os.path.join(os.getcwd(), f"{args.prefix}_output")
    
    # Debugging: Print the output directory
    if args.debug:
        print(f"Debug: Output directory is set to '{args.output_dir}'")
    
    # Create the output directory if it doesn't exist
    try:
        os.makedirs(args.output_dir, exist_ok=True)
    except Exception as e:
        print(f"Error: Could not create output directory '{args.output_dir}': {e}")
        sys.exit(1)
    
    print(f"Processing: {args.input_file}")
    print(f"Output directory: {args.output_dir}")
    print(f"Prefix: {args.prefix}")
    
    # Run diagnostics if requested
    if args.debug:
        diagnose_kml(args.input_file, debug=args.debug)
    
    # Try to repair the file if requested
    input_file = args.input_file
    if args.force:
        input_file = attempt_repair(args.input_file)
    
    # Process the KML file
    try:
        process_kml_file(input_file, args.output_dir, args.prefix, args.debug)
    except Exception as e:
        print(f"Error: Failed to process KML file: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()def process_kml_file(input_file, output_dir, prefix, debug=False):
    """Process a KML file and convert all placemarks to CoT format."""
    try:
        # Parse the input KML file
        parser = etree.XMLParser(recover=True, remove_blank_text=True, resolve_entities=False)
        try:
            tree = etree.parse(input_file, parser)
            root = tree.getroot()
        except etree.XMLSyntaxError as e:
            print(f"Error parsing KML file: {e}")
            return
        
        # Get the main document
        doc = root.find('.//kml:Document', namespaces=NAMESPACES)
        if doc is None:
            doc = root.find('.//Document')
        
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
        
        # Find all placemarks
        placemarks = doc.findall('.//kml:Placemark', namespaces=NAMESPACES)
        if not placemarks:
            placemarks = doc.findall('.//Placemark')
        
        if not placemarks:
            print(f"No placemarks found in {input_file}")
            return
        
        print(f"Found {len(placemarks)} placemarks in {input_file}")
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Process each placemark
        for i, placemark in enumerate(placemarks):
            # Get placemark name
            placemark_name = None
            name_elem = placemark.find('./kml:name', namespaces=NAMESPACES)
            if name_elem is None:
                name_elem = placemark.find('./name')
            
            if name_elem is not None and name_elem.text:
                placemark_name = name_elem.text
            else:
                placemark_name = f"placemark_{i+1}"
            
            print(f"Processing placemark: {placemark_name}")
            
            # Extract style information
            style_info, style_url = extract_style_info(doc, placemark)
            
            # Extract extended data (attributes and description)
            extended_data = extract_extended_data(placemark)
            
            # Create a UID based on consistent values
            uid_base = f"{prefix}_{i:04d}"
            
            # Initialize CoT XML content
            cot_xml = None
            
            # Determine geometry type and extract coordinates
            point_elem = placemark.find('./kml:Point', namespaces=NAMESPACES)
            if point_elem is None:
                point_elem = placemark.find('./Point')
            line_elem = placemark.find('./kml:LineString', namespaces=NAMESPACES) or placemark.find('./LineString')
            polygon_elem = placemark.find('./kml:Polygon', namespaces=NAMESPACES) or placemark.find('./Polygon')
            multi_geom = placemark.find('./kml:MultiGeometry', namespaces=NAMESPACES) or placemark.find('./MultiGeometry')
            
            # Process based on geometry type
            if point_elem is not None:
                # Process Point geometry
                coords = extract_coordinates(point_elem)
                if coords:
                    cot_xml = create_cot_point(placemark_name, coords, (style_info, style_url), extended_data, uid_base)
            
            elif line_elem is not None:
                # Process LineString geometry
                coords = extract_coordinates(line_elem)
                if coords:
                    cot_xml = create_cot_line(placemark_name, coords, (style_info, style_url), extended_data, uid_base)
            
            elif polygon_elem is not None:
                # Process Polygon geometry
                outer_boundary = polygon_elem.find('./kml:outerBoundaryIs', namespaces=NAMESPACES)
                if outer_boundary is None:
                    outer_boundary = polygon_elem.find('./outerBoundaryIs')
                
                if outer_boundary is not None:
                    linear_ring = outer_boundary.find('./kml:LinearRing', namespaces=NAMESPACES)
                    if linear_ring is None:
                        linear_ring = outer_boundary.find('./LinearRing')
                    
                    if linear_ring is not None:
                        coords = extract_coordinates(linear_ring)
                        if coords:
                            cot_xml = create_cot_polygon(placemark_name, coords, (style_info, style_url), extended_data, uid_base)
            
            elif multi_geom is not None:
                # Process MultiGeometry - use the first geometry found
                sub_point = multi_geom.find('./kml:Point', namespaces=NAMESPACES) or multi_geom.find('./Point')
                sub_line = multi_geom.find('./kml:LineString', namespaces=NAMESPACES) or multi_geom.find('./LineString')
                sub_polygon = multi_geom.find('./kml:Polygon', namespaces=NAMESPACES) or multi_geom.find('./Polygon')
                
                if sub_point is not None:
                    coords = extract_coordinates(sub_point)
                    if coords:
                        cot_xml = create_cot_point(placemark_name, coords, (style_info, style_url), extended_data, uid_base)
                
                elif sub_line is not None:
                    coords = extract_coordinates(sub_line)
                    if coords:
                        cot_xml = create_cot_line(placemark_name, coords, (style_info, style_url), extended_data, uid_base)
                
                elif sub_polygon is not None:
                    outer_boundary = sub_polygon.find('./kml:outerBoundaryIs', namespaces=NAMESPACES)
                    if outer_boundary is None:
                        outer_boundary = sub_polygon.find('./outerBoundaryIs')
                    
                    if outer_boundary is not None:
                        linear_ring = outer_boundary.find('./kml:LinearRing', namespaces=NAMESPACES)
                        if linear_ring is None:
                            linear_ring = outer_boundary.find('./LinearRing')
                        
                        if linear_ring is not None:
                            coords = extract_coordinates(linear_ring)
                            if coords:
                                cot_xml = create_cot_polygon(placemark_name, coords, (style_info, style_url), extended_data, uid_base)
            
            # Save CoT XML if generated
            if cot_xml:
                safe_name = sanitize_filename(placemark_name)
                
                # Use .cot extension as seen in the example files
                output_file = os.path.join(output_dir, f"{prefix}_{safe_name}.cot")
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(cot_xml)
                
                print(f"Created CoT file: {output_file}")
            else:
                print(f"Warning: Could not create CoT for {placemark_name}")
        
        print(f"Conversion completed. CoT files saved to {output_dir}")
        
    except Exception as e:
        print(f"Error processing KML file: {e}")
        if debug:
            import traceback
            traceback.print_exc()def attempt_repair(file_path):
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
        return file_pathdef diagnose_kml(file_path, debug=False):
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
        namespaces = {}
        ns_matches = re.findall(r'xmlns:(\w+)="([^"]+)"', content_str)
        for prefix, uri in ns_matches:
            namespaces[prefix] = uri
        
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
            
        # If debug mode, print first 500 chars of content
        if debug:
            print("\nFile content preview:")
            print(content_str[:500])
            print("...")
            
    except Exception as e:
        print(f"Error during diagnostics: {e}")
    
    print("--- End of Diagnostics ---\n")#!/usr/bin/env python3
"""
KML to CoT Converter for ATAK

This script converts KML files to Cursor on Target (CoT) format for use in ATAK.
It handles points (markers), lines (routes), and polygons (shapes) while preserving metadata.

Usage:
    python kml_to_cot.py input.kml [--output OUTPUT_DIR] [--prefix PREFIX] [--debug] [--force]

Options:
    --output    Directory to save output files (default: based on input filename + "_output")
    --prefix    Prefix for output filenames (default: based on input filename)
    --debug     Show detailed diagnostic information
    --force     Attempt to repair malformed KML files

Output:
    Creates CoT (.cot) files for each placemark in the KML file
"""

import sys
import os
import re
import uuid
import argparse
import datetime
import json
import html
from lxml import etree
import xml.etree.ElementTree as ET
from xml.dom import minidom

# Define common KML namespaces
NAMESPACES = {
    'kml': 'http://www.opengis.net/kml/2.2',
    'gx': 'http://www.google.com/kml/ext/2.2',
    'atom': 'http://www.w3.org/2005/Atom',
    'xal': 'urn:oasis:names:tc:ciq:xsdschema:xAL:2.0'
}

# CoT type mapping - maps KML style/elements to CoT types
COT_TYPE_MAPPING = {
    # Default type for unknown features
    'default': 'a-h-G',  # Generic
    # Points/Markers
    'point': {
        'default': 'a-u-G',      # Updated to match the sample files (was: a-h-G-U-C)
        'marker': 'a-u-G',       # Updated to match the sample files
        'pin': 'b-m-p-s-m',      # Updated to match spotmarker in examples
        'icon': 'a-u-G',         # Updated to match the sample files
    },
    # Lines/Routes
    'line': {
        'default': 'u-d-f',        # Route/Freehand drawing
        'route': 'b-m-r',          # Updated to match Route.cot
        'track': 'u-d-f',          # Track
        'extrude': 'u-d-f',        # 3D Route
    },
    # Polygons/Shapes
    'polygon': {
        'default': 'u-d-r',        # Shape - Rectangle
        'shape': 'u-d-r',          # Shape - Rectangle
        'building': 'a-h-S',       # Building
    }
}

def sanitize_filename(name):
    """Convert a name to a valid filename."""
    # Remove invalid filename characters
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    # Replace spaces with underscores
    name = name.replace(' ', '_')
    # Make sure it's not empty
    if not name:
        name = "unnamed_feature"
    return name

def get_cot_type(geometry_type, style_url=None, extended_data=None):
    """Determine the appropriate CoT type based on KML geometry and style."""
    # Start with geometry-based mapping
    type_map = COT_TYPE_MAPPING.get(geometry_type, {})
    
    # Default for this geometry type
    cot_type = type_map.get('default', COT_TYPE_MAPPING['default'])
    
    # Try to refine based on style or extended data
    if style_url and style_url.startswith('#'):
        style_id = style_url[1:].lower()
        
        # Look for keywords in style ID
        for key, value in type_map.items():
            if key != 'default' and key in style_id:
                return value
    
    # Check extended data for type hints
    if extended_data:
        for key, value in extended_data.items():
            key_lower = key.lower()
            value_lower = str(value).lower()
            
            # Check for type indicators in the data
            if 'type' in key_lower:
                for type_key, type_value in type_map.items():
                    if type_key != 'default' and type_key in value_lower:
                        return type_value
    
    return cot_type

def get_cot_color(kml_color=None, style_url=None):
    """Convert KML color to CoT color format."""
    # Default color (ATAK yellow)
    default_color = 'ffff00'
    
    if not kml_color:
        return default_color
    
    # KML colors are AABBGGRR format, CoT uses RRGGBB
    try:
        # Extract color components, ignoring alpha
        if len(kml_color) == 8:
            # AABBGGRR -> RRGGBB
            return kml_color[6:8] + kml_color[4:6] + kml_color[2:4]
        elif len(kml_color) == 6:
            # Assume already in RRGGBB format
            return kml_color
    except:
        pass
    
    return default_color

def extract_extended_data(placemark):
    """Extract extended data from a KML placemark."""
    extended_data = {}
    
    # Try to find ExtendedData element
    ext_data_elem = placemark.find('.//kml:ExtendedData', namespaces=NAMESPACES)
    if ext_data_elem is None:
        ext_data_elem = placemark.find('.//ExtendedData')
    
    if ext_data_elem is not None:
        # Process Data elements
        data_elems = ext_data_elem.findall('.//kml:Data', namespaces=NAMESPACES)
        if not data_elems:
            data_elems = ext_data_elem.findall('.//Data')
        
        for data in data_elems:
            name = data.get('name', '')
            value_elem = data.find('.//kml:value', namespaces=NAMESPACES)
            if value_elem is None:
                value_elem = data.find('.//value')
            
            if value_elem is not None and value_elem.text:
                extended_data[name] = value_elem.text
            elif name:
                # If there's no value element but the Data has a name, store empty string
                extended_data[name] = ''
        
        # Process SimpleData elements (from Schema)
        simple_data_elems = ext_data_elem.findall('.//kml:SimpleData', namespaces=NAMESPACES)
        if not simple_data_elems:
            simple_data_elems = ext_data_elem.findall('.//SimpleData')
        
        for data in simple_data_elems:
            name = data.get('name', '')
            if name and data.text:
                extended_data[name] = data.text
    
    # Extract description data if present
    desc_elem = placemark.find('.//kml:description', namespaces=NAMESPACES)
    if desc_elem is None:
        desc_elem = placemark.find('.//description')
    
    if desc_elem is not None and desc_elem.text:
        extended_data['description'] = desc_elem.text
        
        # Try to extract data from HTML tables in description
        if '<table' in desc_elem.text:
            try:
                # Very simple HTML table parser
                table_matches = re.findall(r'<tr[^>]*>\s*<td[^>]*>(.*?)</td>\s*<td[^>]*>(.*?)</td>', 
                                         desc_elem.text, re.DOTALL | re.IGNORECASE)
                for key, value in table_matches:
                    # Clean HTML tags and whitespace
                    clean_key = re.sub(r'<[^>]+>', '', key).strip()
                    clean_value = re.sub(r'<[^>]+>', '', value).strip()
                    if clean_key and clean_value:
                        extended_data[clean_key] = clean_value
            except Exception as e:
                # Skip if HTML parsing fails
                print(f"Warning: HTML table parsing failed: {e}")
                pass
    
    return extended_data

def extract_style_info(doc, placemark):
    """Extract style information from a KML placemark and referenced styles."""
    style_info = {
        'icon_style': None,
        'line_style': None,
        'poly_style': None,
        'label_style': None,
        'icon_url': None,
        'line_color': None,
        'line_width': None,
        'poly_color': None,
        'label_color': None,
        'scale': None
    }
    
    # Check for direct style URL reference
    style_url_elem = placemark.find('.//kml:styleUrl', namespaces=NAMESPACES)
    if style_url_elem is None:
        style_url_elem = placemark.find('.//styleUrl')
    
    style_url = None
    if style_url_elem is not None and style_url_elem.text:
        style_url = style_url_elem.text
        
        # Find the referenced style
        if style_url.startswith('#'):
            style_id = style_url[1:]
            
            # Try to find the style in the document
            style = doc.find(f'.//kml:Style[@id="{style_id}"]', namespaces=NAMESPACES)
            if style is None:
                style = doc.find(f'.//Style[@id="{style_id}"]')
                
            if style is not None:
                # Extract icon style
                icon_style = style.find('.//kml:IconStyle', namespaces=NAMESPACES)
                if icon_style is None:
                    icon_style = style.find('.//IconStyle')
                
                if icon_style is not None:
                    style_info['icon_style'] = icon_style
                    
                    # Extract icon URL
                    icon_elem = icon_style.find('.//kml:Icon/kml:href', namespaces=NAMESPACES)
                    if icon_elem is None:
                        icon_elem = icon_style.find('.//Icon/href')
                    
                    if icon_elem is not None and icon_elem.text:
                        style_info['icon_url'] = icon_elem.text
                    
                    # Extract scale
                    scale_elem = icon_style.find('.//kml:scale', namespaces=NAMESPACES)
                    if scale_elem is None:
                        scale_elem = icon_style.find('.//scale')
                    
                    if scale_elem is not None and scale_elem.text:
                        try:
                            style_info['scale'] = float(scale_elem.text)
                        except:
                            pass
                
                # Extract line style
                line_style = style.find('.//kml:LineStyle', namespaces=NAMESPACES)
                if line_style is None:
                    line_style = style.find('.//LineStyle')
                
                if line_style is not None:
                    style_info['line_style'] = line_style
                    
                    # Extract line color
                    color_elem = line_style.find('.//kml:color', namespaces=NAMESPACES)
                    if color_elem is None:
                        color_elem = line_style.find('.//color')
                    
                    if color_elem is not None and color_elem.text:
                        style_info['line_color'] = color_elem.text
                    
                    # Extract line width
                    width_elem = line_style.find('.//kml:width', namespaces=NAMESPACES)
                    if width_elem is None:
                        width_elem = line_style.find('.//width')
                    
                    if width_elem is not None and width_elem.text:
                        try:
                            style_info['line_width'] = float(width_elem.text)
                        except:
                            pass
                
                # Extract polygon style
                poly_style = style.find('.//kml:PolyStyle', namespaces=NAMESPACES)
                if poly_style is None:
                    poly_style = style.find('.//PolyStyle')
                
                if poly_style is not None:
                    style_info['poly_style'] = poly_style
                    
                    # Extract polygon color
                    color_elem = poly_style.find('.//kml:color', namespaces=NAMESPACES)
                    if color_elem is None:
                        color_elem = poly_style.find('.//color')
                    
                    if color_elem is not None and color_elem.text:
                        style_info['poly_color'] = color_elem.text
                
                # Extract label style
                label_style = style.find('.//kml:LabelStyle', namespaces=NAMESPACES)
                if label_style is None:
                    label_style = style.find('.//LabelStyle')
                
                if label_style is not None:
                    style_info['label_style'] = label_style
                    
                    # Extract label color
                    color_elem = label_style.find('.//kml:color', namespaces=NAMESPACES)
                    if color_elem is None:
                        color_elem = label_style.find('.//color')
                    
                    if color_elem is not None and color_elem.text:
                        style_info['label_color'] = color_elem.text
    
    # Check for inline styles within the placemark
    inline_style = placemark.find('.//kml:Style', namespaces=NAMESPACES)
    if inline_style is None:
        inline_style = placemark.find('.//Style')
    
    if inline_style is not None:
        # Similar extraction as above but from inline styles
        # Add code for inline style extraction if needed
        pass
    
    return style_info, style_url

def extract_coordinates(geometry_elem):
    """Extract coordinates from a KML geometry element."""
    coords = []

    if geometry_elem is None:
        return coords

    # Find coordinates element with namespace handling
    coords_elem = geometry_elem.find('.//{http://www.opengis.net/kml/2.2}coordinates')
    if coords_elem is None:
        coords_elem = geometry_elem.find('.//coordinates')

    if coords_elem is not None and coords_elem.text:
        # Parse coordinate string
        coord_str = coords_elem.text.strip()
        if not coord_str:  # Handle empty coordinates
            print("Warning: Empty <coordinates> tag found. Skipping element.")
            return coords

        coord_parts = coord_str.split()

        for part in coord_parts:
            values = part.strip().split(',')
            if len(values) >= 2:
                try:
                    lon = float(values[0])
                    lat = float(values[1])
                    # Handle optional altitude
                    alt = 0.0
                    if len(values) >= 3 and values[2]:
                        try:
                            alt = float(values[2])
                        except:
                            pass

                    coords.append((lon, lat, alt))
                except:
                    # Skip invalid coordinates
                    pass
    else:
        print("Warning: Missing <coordinates> tag. Skipping element.")

    return coords

def sanitize_html_content(content):
    """Safely sanitize HTML content by removing tags and correctly escaping XML special characters."""
    if not content:
        return ""
    
    try:
        # Remove all HTML tags, keeping only the text content
        text_content = re.sub(r'<[^>]+>', ' ', content)
        # Normalize whitespace - replace multiple spaces with a single space
        text_content = re.sub(r'\s+', ' ', text_content).strip()
        # Unescape HTML entities like &lt; to < first
        unescaped = html.unescape(text_content)
        # Escape XML special characters
        sanitized = unescaped.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&apos;')
        return sanitized
    except Exception as e:
        print(f"Error sanitizing content: {e}")
        return "Invalid content"

def create_cot_point(name, coords, style_info, extended_data, uid=None):
    """Create a CoT XML for a point/marker that matches ATAK format."""
    if not coords or len(coords) == 0:
        return None

    # Use first coordinate for point
    lon, lat, alt = coords[0]

    # Generate a unique ID if not provided
    if not uid:
        uid = str(uuid.uuid4())

    # Create root event element
    root = ET.Element('event')
    root.set('version', '2.0')
    root.set('uid', uid)
    root.set('type', get_cot_type('point', style_info[1], extended_data))
    
    # Set time attributes - current time plus 14 days stale time (matching examples)
    now = datetime.datetime.now(datetime.UTC)
    stale_time = now + datetime.timedelta(days=14)
    
    time_str = now.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    stale_str = stale_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    
    root.set('time', time_str)
    root.set('start', time_str)
    root.set('stale', stale_str)
    root.set('how', 'h-g-i-g-o')  # How: Human input, GPS, Internet, GPS, Other

    # Add point information
    point = ET.SubElement(root, 'point')
    point.set('lat', str(lat))
    point.set('lon', str(lon))
    point.set('hae', str(alt))  # Height above ellipsoid
    point.set('ce', '9999999.0')  # Circular error (not specified)
    point.set('le', '9999999.0')  # Linear error (not specified)

    # Add detail section
    detail = ET.SubElement(root, 'detail')
    
    # Add status readiness (matching examples)
    status = ET.SubElement(detail, 'status')
    status.set('readiness', 'true')
    
    # Add archive tag (matching examples)
    ET.SubElement(detail, 'archive')

    # Add contact info
    contact = ET.SubElement(detail, 'contact')
    contact.set('callsign', name)

    # Add remarks with description if available
    if 'description' in extended_data:
        remarks = ET.SubElement(detail, 'remarks')
        remarks.text = ""  # Empty remarks like in examples
    
    # Add archive tag again (matching examples)
    ET.SubElement(detail, 'archive')

    # Add color
    color = ET.SubElement(detail, 'color')
    color.set('argb', '-1')  # Default white color with alpha
    
    # Add precision location
    precision = ET.SubElement(detail, 'precisionlocation')
    precision.set('altsrc', '???')
    
    # Add usericon if we have style info
    if style_info[0].get('icon_url'):
        usericon = ET.SubElement(detail, 'usericon')
        # Convert KML icon path to a suitable ATAK path
        icon_path = style_info[0].get('icon_url')
        icon_name = os.path.basename(icon_path)
        usericon.set('iconsetpath', f'f7f71666-8b28-4b57-9fbb-e38e61d33b79/Google/{icon_name}')

    # Format the XML string with pretty printing
    try:
        rough_string = ET.tostring(root, 'utf-8')
        parsed = minidom.parseString(rough_string)
        pretty_xml = parsed.toprettyxml(indent='\t')
        # Fix XML declaration to match examples
        pretty_xml = pretty_xml.replace('<?xml version="1.0" ?>', '<?xml version=\'1.0\' encoding=\'UTF-8\' standalone=\'yes\'?>')
        return pretty_xml
    except Exception as e:
        print(f"Error serializing XML for {name}: {e}")
        return None

def create_cot_line(name, coords, style_info, extended_data, uid=None):
    """Create a CoT XML for a line/route that matches ATAK format."""
    if not coords or len(coords) < 2:
        return None
    
    # Generate a unique ID if not provided
    if not uid:
        uid = str(uuid.uuid4())
    
    # Create root event element
    root = ET.Element('event')
    root.set('version', '2.0')
    root.set('uid', uid)
    root.set('type', get_cot_type('line', style_info[1], extended_data))
    
    # Set time attributes - current time plus 1 day stale time
    now = datetime.datetime.now(datetime.UTC)
    stale_time = now + datetime.timedelta(days=1)
    
    time_str = now.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    stale_str = stale_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    
    root.set('time', time_str)
    root.set('start', time_str)
    root.set('stale', stale_str)
    root.set('how', 'h-e')  # Changed to match example
    
    # Add point information - freehand lines use 0,0 as the point
    point = ET.SubElement(root, 'point')
    point.set('lat', '0.0')
    point.set('lon', '0.0')
    point.set('hae', '9999999.0')
    point.set('ce', '9999999.0')
    point.set('le', '9999999.0')
    
    # Add detail section
    detail = ET.SubElement(root, 'detail')
    
    # Add all points as links - format depends on type
    if 'route' in style_info[1].lower():
        # Route format - more complex with UID and type
        for i, (lon, lat, alt) in enumerate(coords):
            link = ET.SubElement(detail, 'link')
            # Generate a unique ID for each point
            point_uid = str(uuid.uuid4())
            link.set('uid', point_uid)
            
            # First and last points get waypoint type, others are control points
            if i == 0 or i == len(coords) - 1:
                link.set('type', 'b-m-p-w')  # Waypoint type
                link.set('callsign', f'CP{i+1}' if i > 0 else f'{name} SP')
            else:
                link.set('type', 'b-m-p-c')  # Control point type
                link.set('callsign', '')
                
            link.set('point', f'{lat},{lon},{alt}')
            link.set('remarks', '')
            link.set('relation', 'c')  # Relationship is 'c' (connect)
            
        # Add route attributes
        link_attr = ET.SubElement(detail, 'link_attr')
        link_attr.set('planningmethod', 'Infil')
        link_attr.set('color', '-1')
        link_attr.set('method', 'Driving')
        link_attr.set('prefix', 'CP')
        link_attr.set('type', 'Vehicle')
        link_attr.set('stroke', '3')
        link_attr.set('direction', 'Infil')
        link_attr.set('routetype', 'Primary')
        link_attr.set('order', 'Ascending Check Points')
    else:
        # Standard line/freehand format - simpler 
        link_line = ET.SubElement(detail, 'link')
        
        # For freehand lines, embed an entire event in the line attribute
        inner_event = ET.Element('event')
        inner_event.set('version', '2.0')
        inner_event.set('uid', str(uuid.uuid4()))
        inner_event.set('type', 'u-d-f')
        inner_event.set('time', time_str)
        inner_event.set('start', time_str)
        inner_event.set('stale', stale_str)
        inner_event.set('how', 'h-e')
        
        # Use first coordinate for inner point
        lon, lat, alt = coords[0]
        inner_point = ET.SubElement(inner_event, 'point')
        inner_point.set('lat', str(lat))
        inner_point.set('lon', str(lon))
        inner_point.set('hae', str(alt))
        inner_point.set('ce', '9999999.0')
        inner_point.set('le', '9999999.0')
        
        # Add inner detail section
        inner_detail = ET.SubElement(inner_event, 'detail')
        
        # Add points as links in inner detail
        for lon, lat, alt in coords:
            inner_link = ET.SubElement(inner_detail, 'link')
            inner_link.set('point', f'{lat},{lon},{alt}')
        
        # Add style elements to inner detail
        inner_stroke_color = ET.SubElement(inner_detail, 'strokeColor')
        inner_stroke_color.set('value', '-1')  # Default white color
        
        inner_stroke_weight = ET.SubElement(inner_detail, 'strokeWeight')
        inner_stroke_weight.set('value', '4.0')  # Line width
        
        inner_contact = ET.SubElement(inner_detail, 'contact')
        inner_contact.set('callsign', name)
        
        ET.SubElement(inner_detail, 'archive')
        
        inner_labels = ET.SubElement(inner_detail, 'labels_on')
        inner_labels.set('value', 'false')
        
        # Convert inner event to string and set as line attribute
        inner_xml = ET.tostring(inner_event, encoding='unicode')
        # Escape XML entities for embedding
        inner_xml = inner_xml.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&apos;')
        link_line.set('line', inner_xml)
    
    # Add common elements for all line types
    stroke_color = ET.SubElement(detail, 'strokeColor')
    stroke_color.set('value', '-1')  # Default white color
    
    stroke_weight = ET.SubElement(detail, 'strokeWeight')
    stroke_weight.set('value', '4.0' if 'route' not in style_info[1].lower() else '3.0')  # Line width
    
    # Add route info for routes
    if 'route' in style_info[1].lower():
        route_info = ET.SubElement(detail, '__routeinfo')
        nav_cues = ET.SubElement(route_info, '__navcues')
    
    # Add contact info
    contact = ET.SubElement(detail, 'contact')
    contact.set('callsign', name)
    
    # Add remarks
    remarks = ET.SubElement(detail, 'remarks')
    remarks.text = ""  # Empty in examples
    
    # Add archive tag
    ET.SubElement(detail, 'archive')
    
    # Add labels flag
    labels_on = ET.SubElement(detail, 'labels_on')
    labels_on.set('value', 'false')
    
    # Add color
    color = ET.SubElement(detail, 'color')
    color.set('value', '-1')  # Default white color
    
    # Format the XML string with pretty printing
    try:
        rough_string = ET.tostring(root, 'utf-8')
        parsed = minidom.parseString(rough_string)
        pretty_xml = parsed.toprettyxml(indent='\t')
        # Fix XML declaration to match examples
        pretty_xml = pretty_xml.replace('<?xml version="1.0" ?>', '<?xml version=\'1.0\' encoding=\'UTF-8\' standalone=\'yes\'?>')
        return pretty_xml
    except Exception as e:
        print(f"Error serializing XML for {name}: {e}")
        return None

def create_cot_polygon(name, coords, style_info, extended_data, uid=None):
    """Create a CoT XML for a polygon/shape that matches ATAK format."""
    if not coords or len(coords) < 3:
        try:
            # Make sure polygon is closed
            if coords[0] != coords[-1]:
                coords.append(coords[0])
        except:
            raise ValueError("Invalid coordinates for polygon")
    
    # Generate a unique ID if not provided
    if not uid:
        uid = str(uuid.uuid4())
    
    # Create root event element
    root = ET.Element('event')
    root.set('version', '2.0')
    root.set('uid', uid)
    root.set('type', 'u-d-r')  # Using rectangle type from examples
    
    # Set time attributes - current time plus 1 day stale time
    now = datetime.datetime.now(datetime.UTC)
    stale_time = now + datetime.timedelta(days=1)
    
    time_str = now.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    stale_str = stale_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    
    root.set('time', time_str)
    root.set('start', time_str)
    root.set('stale', stale_str)
    root.set('how', 'h-e')  # How based on examples
    
    # Use centroid for the point element
    avg_lon = sum([c[0] for c in coords]) / len(coords)
    avg_lat = sum([c[1] for c in coords]) / len(coords)
    avg_alt = sum([c[2] for c in coords]) / len(coords)
    
    # Add point information (centroid)
    point = ET.SubElement(root, 'point')
    point.set('lat', str(avg_lat))
    point.set('lon', str(avg_lon))
    point.set('hae', '9999999.0')  # Match examples
    point.set('ce', '9999999.0')  # Match examples
    point.set('le', '9999999.0')  # Match examples
    
    # Add detail section
    detail = ET.SubElement(root, 'detail')
    
    # Add all polygon points as links
    for lon, lat, alt in coords:
        link = ET.SubElement(detail, 'link')
        link.set('point', f'{lat},{lon}')
    
    # Add style elements
    stroke_color = ET.SubElement(detail, 'strokeColor')
    stroke_color.set('value', '-1')  # White
    
    stroke_weight = ET.SubElement(detail, 'strokeWeight')
    stroke_weight.set('value', '3.0')  # Line width
    
    # Add fill color
    fill_color = ET.SubElement(detail, 'fillColor')
    fill_color.set('value', '-1761607681')  # Matches examples
    
    # Add contact info
    contact = ET.SubElement(detail, 'contact')
    contact.set('callsign', name)
    
    # Add tog element (matching examples)
    tog = ET.SubElement(detail, 'tog')
    tog.set('enabled', '0')
    
    # Add remarks
    remarks = ET.SubElement(detail, 'remarks')
    remarks.text = ""  # Empty in examples
    
    # Add archive tag
    ET.SubElement(detail, 'archive')
    
    # Add labels flag
    labels_on = ET.SubElement(detail, 'labels_on')
    labels_on.set('value', 'false')
    
    # Add precision location
    precision = ET.SubElement(detail, 'precisionlocation')
    precision.set('altsrc', '???')
    
    # Format the XML string with pretty printing
    try:
        rough_string = ET.tostring(root, 'utf-8')
        parsed = minidom.parseString(rough_string)
        pretty_xml = parsed.toprettyxml(indent='\t')
        # Fix XML declaration to match examples
        pretty_xml = pretty_xml.replace('<?xml version="1.0" ?>', '<?xml version=\'1.0\' encoding=\'UTF-8\' standalone=\'yes\'?>')
        return pretty_xml
    except Exception as e:
        print(f"Error serializing XML for {name}: {e}")
        return None