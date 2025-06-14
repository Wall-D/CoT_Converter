import re
import datetime

def sanitize_filename(name):
    """Convert a name to a valid filename."""
    if not name:
        return "unnamed_feature"
        
    # Remove invalid characters and replace spaces with underscores
    sanitized = re.sub(r'[\\/*?:"<>|]', "", name).replace(' ', '_')
    
    # Remove any non-ASCII characters
    sanitized = re.sub(r'[^\x00-\x7F]+', '', sanitized)
    
    # Ensure the filename is not empty after sanitization
    return sanitized.strip('_') or "unnamed_feature"

def get_current_time():
    """Get the current time in ISO 8601 format."""
    return datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')

def get_stale_time(hours=24):
    """Get the stale time (default 24 hours from now) in ISO 8601 format."""
    return (datetime.datetime.utcnow() + datetime.timedelta(hours=hours)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')

def sanitize_html_content(content):
    """Sanitize HTML content by removing tags and escaping special characters."""
    text_content = re.sub(r'<[^>]+>', ' ', content)
    return text_content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

if __name__ == "__main__":
    print("This module provides utility functions for the KML to CoT converter.")