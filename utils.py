import re
import datetime

def sanitize_filename(name):
    """Convert a name to a valid filename."""
    name = re.sub(r'[\\/*?:"<>|]', "", name).replace(' ', '_')
    return name or "unnamed_feature"

def get_current_time():
    """Get the current time in ISO 8601 format."""
    return datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')

def get_stale_time():
    """Get the stale time (1 hour from now) in ISO 8601 format."""
    return (datetime.datetime.utcnow() + datetime.timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')

def sanitize_html_content(content):
    """Sanitize HTML content by removing tags and escaping special characters."""
    text_content = re.sub(r'<[^>]+>', ' ', content)
    return text_content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

if __name__ == "__main__":
    print("This module provides utility functions for the KML to CoT converter.")