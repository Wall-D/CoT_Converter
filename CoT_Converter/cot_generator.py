from .utils import sanitize_filename, get_current_time, get_stale_time
from .kml_parser import NAMESPACES, extract_coordinates, extract_polygon_coordinates, calculate_centroid
import os
import uuid

def generate_uid():
    """Generate a unique identifier for CoT events."""
    return str(uuid.uuid4())

def convert_kml_color_to_cot(kml_color):
    """Convert KML AABBGGRR color to COT ARGB format."""
    try:
        if not kml_color or len(kml_color) != 8:
            raise ValueError("Invalid color format")
            
        if not all(c in '0123456789ABCDEFabcdef' for c in kml_color):
            raise ValueError("Invalid hex characters")
        
        # KML format: AABBGGRR -> COT format: AARRGGBB
        aa = kml_color[0:2]  # Alpha
        bb = kml_color[2:4]  # Blue
        gg = kml_color[4:6]  # Green  
        rr = kml_color[6:8]  # Red
        
        cot_color = aa + rr + gg + bb
        return str(int(cot_color, 16) - 2**32)  # Convert to signed integer
    except (ValueError, TypeError) as e:
        print(f"Warning: Invalid color value '{kml_color}': {e}")
        return '-16777216'  # Default black

def validate_coordinates(lat, lon, hae=None):
    """Validate coordinate values."""
    try:
        lat = float(lat)
        lon = float(lon)
        if hae is not None:
            hae = float(hae)
            
        if not (-90 <= lat <= 90):
            raise ValueError(f"Invalid latitude: {lat}")
        if not (-180 <= lon <= 180):
            raise ValueError(f"Invalid longitude: {lon}")
            
        return True
    except (ValueError, TypeError) as e:
        print(f"Warning: Invalid coordinates (lat={lat}, lon={lon}): {e}")
        return False

def extract_style_info(placemark, root):
    """Extract style information from placemark."""
    style_url = placemark.find('./kml:styleUrl', namespaces=NAMESPACES)
    if style_url is not None and style_url.text:
        style_id = style_url.text.lstrip('#')
        style_elem = root.find(f'.//kml:Style[@id="{style_id}"]', namespaces=NAMESPACES)
        if style_elem is not None:
            return parse_style_element(style_elem)
    return {}

def parse_style_element(style_elem):
    """Parse KML Style element for colors and line width."""
    style_info = {}
    
    # Line style
    line_style = style_elem.find('./kml:LineStyle', namespaces=NAMESPACES)
    if line_style is not None:
        color_elem = line_style.find('./kml:color', namespaces=NAMESPACES)
        width_elem = line_style.find('./kml:width', namespaces=NAMESPACES)
        
        if color_elem is not None:
            style_info['stroke_color'] = convert_kml_color_to_cot(color_elem.text)
        if width_elem is not None:
            style_info['stroke_weight'] = width_elem.text
    
    # Polygon style
    poly_style = style_elem.find('./kml:PolyStyle', namespaces=NAMESPACES)
    if poly_style is not None:
        color_elem = poly_style.find('./kml:color', namespaces=NAMESPACES)
        if color_elem is not None:
            style_info['fill_color'] = convert_kml_color_to_cot(color_elem.text)
    
    return style_info

def process_placemarks(placemarks, output_dir, prefix, debug=False):
    """Enhanced placemark processing for multiple geometry types."""
    for i, placemark in enumerate(placemarks):
        placemark_name = placemark.find('./kml:name', namespaces=NAMESPACES)
        if placemark_name is None or not placemark_name.text:
            placemark_name = f"placemark_{i+1}"
        else:
            placemark_name = placemark_name.text

        # Check for different geometry types
        point_elem = placemark.find('.//kml:Point', namespaces=NAMESPACES)
        polygon_elem = placemark.find('.//kml:Polygon', namespaces=NAMESPACES)
        linestring_elem = placemark.find('.//kml:LineString', namespaces=NAMESPACES)
        
        cot_xml = None
        uid = generate_uid()  # Generate a unique UID for the CoT file
        
        if polygon_elem is not None:
            coords = extract_polygon_coordinates(polygon_elem)
            if coords:
                cot_xml = create_cot_polygon(placemark_name, coords, prefix)
                
        elif point_elem is not None:
            coords = extract_coordinates(point_elem)
            if coords:
                cot_xml = create_cot_point(placemark_name, coords, prefix)
                
        elif linestring_elem is not None:
            coords = extract_coordinates(linestring_elem)
            if coords:
                cot_xml = create_cot_linestring(placemark_name, coords, prefix)
        
        if cot_xml:
            save_cot_file(cot_xml, output_dir, uid, placemark_name)
        elif debug:
            print(f"Warning: No supported geometry found for placemark: {placemark_name}")

def create_cot_point(name, coords, prefix, icon_type='a-u-G'):
    """Create CoT XML for a point."""
    lat, lon, hae = coords[0]
    if not validate_coordinates(lat, lon, hae):
        return None
        
    uid = generate_uid()
    current_time = get_current_time()
    stale_time = get_stale_time()
    
    return f"""<?xml version='1.0' encoding='UTF-8' standalone='yes'?>
<event version='2.0' uid='{uid}' type='{icon_type}' time='{current_time}' start='{current_time}' stale='{stale_time}' how='h-g-i-g-o'>
    <point lat='{lat}' lon='{lon}' hae='{hae}' ce='9999999.0' le='9999999.0' />
    <detail>
        <status readiness='true'/>
        <archive/>
        <contact callsign='{name}'/>
        <remarks></remarks>
        <archive/>
        <color argb='-1'/>
        <precisionlocation altsrc='???'/>
        <usericon iconsetpath='COT_MAPPING_2525B/a-u/a-u-G'/>
    </detail>
</event>"""

def create_cot_polygon(name, coordinates, prefix):
    """Create CoT XML for a polygon."""
    if not coordinates:
        return None
    
    # Calculate centroid for main point
    centroid = calculate_centroid(coordinates)
    if not centroid:
        return None
    
    lat, lon, hae = centroid
    uid = generate_uid()
    current_time = get_current_time()
    stale_time = get_stale_time(hours=24)  # 24 hour stale time for shapes
    
    # Build link points for polygon boundary
    link_points = []
    for coord in coordinates:
        link_points.append(f'        <link point="{coord[0]},{coord[1]},{coord[2]}"/>')
    
    return f"""<?xml version='1.0' encoding='UTF-8' standalone='yes'?>
<event version='2.0' uid='{uid}' type='u-d-f' time='{current_time}' start='{current_time}' stale='{stale_time}' how='h-e'>
    <point lat='{lat}' lon='{lon}' hae='{hae}' ce='9999999.0' le='9999999.0' />
    <detail>
{chr(10).join(link_points)}
        <strokeColor value='-1'/>
        <strokeWeight value='4.0'/>
        <fillColor value='-1761607681'/>
        <contact callsign='{name}'/>
        <remarks></remarks>
        <archive/>
        <labels_on value='false'/>
        <color value='-1'/>
        <precisionlocation altsrc='???'/>
    </detail>
</event>"""

def create_cot_linestring(name, coordinates, prefix):
    """Create CoT XML for a LineString."""
    if not coordinates:
        return None

    # Calculate the midpoint of the LineString for the main point
    midpoint_index = len(coordinates) // 2
    lat, lon, hae = coordinates[midpoint_index]
    uid = generate_uid()
    current_time = get_current_time()
    stale_time = get_stale_time(hours=24)  # 24 hour stale time for shapes

    # Build link points for the LineString path
    link_points = []
    for coord in coordinates:
        link_points.append(f'        <link point="{coord[0]},{coord[1]},{coord[2]}"/>')

    return f"""<?xml version='1.0' encoding='UTF-8' standalone='yes'?>
<event version='2.0' uid='{uid}' type='u-d-l' time='{current_time}' start='{current_time}' stale='{stale_time}' how='h-e'>
    <point lat='{lat}' lon='{lon}' hae='{hae}' ce='9999999.0' le='9999999.0' />
    <detail>
{chr(10).join(link_points)}
        <strokeColor value='-1'/>
        <strokeWeight value='3.0'/>
        <contact callsign='{name}'/>
        <remarks></remarks>
        <archive/>
        <labels_on value='false'/>
        <color value='-1'/>
        <precisionlocation altsrc='???'/>
    </detail>
</event>"""

def create_cot_rectangle(name, coordinates, prefix):
    """Create CoT XML for a rectangle."""
    if not coordinates or len(coordinates) < 4:
        return None

    # Calculate centroid for main point
    centroid = calculate_centroid(coordinates)
    if not centroid:
        return None
    
    lat, lon, hae = centroid
    uid = generate_uid()
    current_time = get_current_time()
    stale_time = get_stale_time(hours=24)  # 24 hour stale time for shapes

    # Build link points for rectangle corners
    link_points = []
    for coord in coordinates[:4]:  # Use only first 4 points for rectangle
        link_points.append(f'        <link point="{coord[0]},{coord[1]},{coord[2]}"/>')

    return f"""<?xml version='1.0' encoding='UTF-8' standalone='yes'?>
<event version='2.0' uid='{uid}' type='u-d-r' time='{current_time}' start='{current_time}' stale='{stale_time}' how='h-e'>
    <point lat='{lat}' lon='{lon}' hae='{hae}' ce='9999999.0' le='9999999.0' />
    <detail>
{chr(10).join(link_points)}
        <strokeColor value='-1'/>
        <strokeWeight value='3.0'/>
        <fillColor value='-1761607681'/>
        <contact callsign='{name}'/>
        <tog enabled='0'/>
        <remarks></remarks>
        <archive/>
        <labels_on value='false'/>
        <precisionlocation altsrc='???'/>
    </detail>
</event>"""

def create_cot_route(name, coordinates, checkpoints, prefix):
    """Create CoT XML for a route with checkpoints."""
    if not coordinates:
        return None

    uid = generate_uid()
    current_time = get_current_time()
    stale_time = get_stale_time(hours=24)

    # Create link elements for each checkpoint
    link_elements = []
    for i, coord in enumerate(coordinates):
        point_uid = generate_uid()
        callsign = checkpoints.get(i, '')
        point_type = 'b-m-p-w' if callsign else 'b-m-p-c'
        link_elements.append(
            f'        <link uid="{point_uid}" callsign="{callsign}" type="{point_type}" '
            f'point="{coord[0]},{coord[1]},{coord[2]}" remarks="" relation="c"/>'
        )

    return f"""<?xml version='1.0' encoding='UTF-8' standalone='yes'?>
<event version='2.0' uid='{uid}' type='b-m-r' time='{current_time}' start='{current_time}' stale='{stale_time}' how='h-e'>
    <point lat='0.0' lon='0.0' hae='9999999.0' ce='9999999.0' le='9999999.0' />
    <detail>
{chr(10).join(link_elements)}
        <link_attr planningmethod='Infil' color='-1' method='Driving' prefix='CP' type='Vehicle' stroke='3' direction='Infil' routetype='Primary' order='Ascending Check Points'/>
        <strokeColor value='-1'/>
        <strokeWeight value='3.0'/>
        <__routeinfo>
            <__navcues/>
        </__routeinfo>
        <contact callsign='{name}'/>
        <remarks></remarks>
        <archive/>
        <labels_on value='false'/>
        <color value='-1'/>
    </detail>
</event>"""

def save_cot_file(cot_xml, output_dir, uid, callsign):
    """Save CoT XML to a file using UID as the filename."""
    safe_uid = sanitize_filename(uid)  # Ensure UID is safe for filenames
    output_file = os.path.join(output_dir, f"{safe_uid}.cot")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(cot_xml)
    print(f"Created CoT file: {output_file}")

if __name__ == "__main__":
    print("This module provides functions for generating CoT files.")