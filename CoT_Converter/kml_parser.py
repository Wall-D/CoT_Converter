import os
import re
from lxml import etree
from .utils import sanitize_html_content

# Define default namespaces
NAMESPACES = {
    'kml': 'http://www.opengis.net/kml/2.2',
    'gx': 'http://www.google.com/kml/ext/2.2',
    'atom': 'http://www.w3.org/2005/Atom',
    'xal': 'urn:oasis:names:tc:ciq:xsdschema:xAL:2.0'
}

def extract_coordinates(geometry_element):
    """Extract coordinates from a KML geometry element (Point, LineString, etc.)."""
    if geometry_element is None:
        return None

    # Find the <coordinates> tag
    coordinates_text = geometry_element.find('./kml:coordinates', namespaces=NAMESPACES)
    if coordinates_text is None or coordinates_text.text is None:
        return None

    # Parse the coordinates (longitude, latitude, altitude)
    coordinates = []
    try:
        for coord in coordinates_text.text.strip().split():
            parts = coord.split(',')
            if len(parts) < 2:
                continue
            
            lon = float(parts[0])
            lat = float(parts[1])
            
            # Validate coordinate ranges
            if not (-180 <= lon <= 180) or not (-90 <= lat <= 90):
                continue
                
            hae = float(parts[2]) if len(parts) > 2 else 0.0
            coordinates.append((lat, lon, hae))
    except ValueError as e:
        print(f"Warning: Invalid coordinate format: {e}")
        return None

    return coordinates if coordinates else None

def extract_polygon_coordinates(polygon_element):
    """Extract coordinates from a KML Polygon element."""
    if polygon_element is None:
        return None
    
    # Find outer boundary coordinates
    outer_boundary = polygon_element.find('.//kml:outerBoundaryIs/kml:LinearRing/kml:coordinates', namespaces=NAMESPACES)
    if outer_boundary is None or outer_boundary.text is None:
        return None
    
    coordinates = []
    coord_pairs = outer_boundary.text.strip().split()
    for coord_pair in coord_pairs:
        if coord_pair.strip():
            parts = coord_pair.split(',')
            if len(parts) >= 2:
                lon, lat = float(parts[0]), float(parts[1])
                alt = float(parts[2]) if len(parts) > 2 else 0.0
                coordinates.append((lat, lon, alt))
    
    return coordinates

def calculate_centroid(coordinates):
    """Calculate the centroid of a polygon."""
    if not coordinates:
        return None
    
    lat_sum = sum(coord[0] for coord in coordinates)
    lon_sum = sum(coord[1] for coord in coordinates)
    alt_sum = sum(coord[2] for coord in coordinates)
    count = len(coordinates)
    
    return (lat_sum/count, lon_sum/count, alt_sum/count)

def extract_linestring_coordinates(linestring_element):
    """Extract coordinates from a KML LineString element."""
    if linestring_element is None:
        return None

    # Find the <coordinates> tag within the LineString element
    coordinates_text = linestring_element.find('./kml:coordinates', namespaces=NAMESPACES)
    if coordinates_text is None or coordinates_text.text is None:
        return None

    # Parse the coordinates (longitude, latitude, altitude)
    coordinates = []
    coord_pairs = coordinates_text.text.strip().split()
    for coord_pair in coord_pairs:
        if coord_pair.strip():
            parts = coord_pair.split(',')
            if len(parts) >= 2:
                lon, lat = float(parts[0]), float(parts[1])
                alt = float(parts[2]) if len(parts) > 2 else 0.0
                coordinates.append((lat, lon, alt))

    return coordinates

def parse_kml_file(file_path, debug=False):
    """Parse KML file and return placemarks."""
    try:
        tree = etree.parse(file_path)
        root = tree.getroot()
        
        # Find all placemarks
        placemarks = root.xpath('//kml:Placemark', namespaces=NAMESPACES)
        
        if debug:
            print(f"Found {len(placemarks)} placemarks")
            
        return placemarks, root  # Return root for style parsing
        
    except Exception as e:
        raise Exception(f"Failed to parse KML file: {e}")

def diagnose_kml(file_path):
    """Diagnostic function for KML files."""
    print(f"Diagnosing KML file: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check for basic XML syntax
        try:
            tree = etree.parse(file_path)
        except etree.XMLSyntaxError as e:
            print(f"XML Syntax Error: {e}")
            return False
            
        # Check for required KML elements
        root = tree.getroot()
        if not root.tag.endswith('}kml'):
            print("Error: Not a valid KML file (missing kml root element)")
            return False
            
        # Check for Document or Folder
        if not root.find('.//kml:Document', namespaces=NAMESPACES) and \
           not root.find('.//kml:Folder', namespaces=NAMESPACES):
            print("Warning: No Document or Folder elements found")
            
        # Check for Placemarks
        placemarks = root.findall('.//kml:Placemark', namespaces=NAMESPACES)
        if not placemarks:
            print("Warning: No Placemarks found in the file")
            
        print("Diagnosis complete")
        return True
            
    except Exception as e:
        print(f"Error during diagnosis: {e}")
        return False

def attempt_repair(file_path):
    """Attempt to repair malformed KML."""
    print(f"Attempting to repair: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Try to fix common issues
        # 1. Add missing XML declaration
        if not content.strip().startswith('<?xml'):
            content = '<?xml version="1.0" encoding="UTF-8"?>\n' + content
            
        # 2. Fix missing or incorrect namespace declarations
        if 'xmlns=' not in content and '<kml' in content:
            content = content.replace('<kml', '<kml xmlns="http://www.opengis.net/kml/2.2"')
            
        # 3. Close unclosed tags
        parser = etree.XMLParser(recover=True)
        tree = etree.fromstring(content.encode('utf-8'), parser)
        
        # Save repaired content to a new file
        repaired_path = file_path + '.repaired'
        with open(repaired_path, 'wb') as f:
            f.write(etree.tostring(tree, pretty_print=True))
            
        print(f"Repaired file saved as: {repaired_path}")
        return repaired_path
            
    except Exception as e:
        print(f"Failed to repair file: {e}")
        return file_path  # Return original file if repair fails

if __name__ == "__main__":
    print("This module provides functions for parsing KML files.")