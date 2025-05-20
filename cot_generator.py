import os
from kml_parser import NAMESPACES, extract_coordinates  # Import extract_coordinates
from utils import sanitize_filename, get_current_time, get_stale_time

def process_placemarks(placemarks, output_dir, prefix, debug=False):
    """Process placemarks and generate CoT files."""
    for i, placemark in enumerate(placemarks):
        placemark_name = placemark.find('./kml:name', namespaces=NAMESPACES)
        if placemark_name is None or not placemark_name.text:
            placemark_name = f"placemark_{i+1}"
        else:
            placemark_name = placemark_name.text

        # Generate CoT XML (example for points)
        coords = extract_coordinates(placemark.find('./kml:Point', namespaces=NAMESPACES))
        if coords:
            cot_xml = create_cot_point(placemark_name, coords, prefix)
            save_cot_file(cot_xml, output_dir, prefix, placemark_name)

def create_cot_point(name, coords, prefix):
    """Create CoT XML for a point."""
    lat, lon, hae = coords[0]
    uid = f"{prefix}_{name}"
    return f"""<?xml version='1.0' encoding='UTF-8' standalone='yes'?>
<event version='2.0' uid='{uid}' type='a-u-G' time='{get_current_time()}' start='{get_current_time()}' stale='{get_stale_time()}' how='h-g-i-g-o'>
  <point lat='{lat}' lon='{lon}' hae='{hae}' ce='9999999.0' le='9999999.0' />
  <detail>
    <contact callsign='{name}' />
  </detail>
</event>
"""

def save_cot_file(cot_xml, output_dir, prefix, name):
    """Save CoT XML to a file."""
    safe_name = sanitize_filename(name)
    output_file = os.path.join(output_dir, f"{prefix}_{safe_name}.cot")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(cot_xml)
    print(f"Created CoT file: {output_file}")

if __name__ == "__main__":
    print("This module provides functions for generating CoT files.")