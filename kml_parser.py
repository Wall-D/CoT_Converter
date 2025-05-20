import os
import re
from lxml import etree
from utils import sanitize_html_content

# Define default namespaces if not already defined
try:
    NAMESPACES
except NameError:
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
    for coord in coordinates_text.text.strip().split():
        lon, lat, *alt = map(float, coord.split(','))
        hae = alt[0] if alt else 0.0  # Default altitude to 0.0 if not provided
        coordinates.append((lat, lon, hae))

    return coordinates

if __name__ == "__main__":
    print("This module provides functions for parsing KML files.")