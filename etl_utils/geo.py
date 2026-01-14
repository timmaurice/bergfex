"""
Geolocation utilities for parsing coordinates from URLs and HTML.
"""
import logging
import re
from urllib.parse import parse_qs, urlparse

_LOGGER = logging.getLogger(__name__)


def extract_coords(url: str, html: str | None = None) -> tuple[float, float] | None:
    """
    Extract latitude and longitude from a URL or HTML content.
    
    Strategies:
    1. Check URL fragment for 'mapstate' parameter.
    2. Check HTML for 'destination' parameter (Google Maps link).
    
    Args:
        url: The URL to check (for fragment).
        html: Optional HTML content to check (for destination link).
        
    Returns:
        tuple[float, float] or None: (latitude, longitude) if found, else None.
    """
    # Strategy 1: URL Fragment
    coords = _from_mapstate(url)
    if coords:
        return coords
        
    # Strategy 2: HTML Content
    if html:
        coords = _from_html(html)
        if coords:
            return coords
            
    return None


def _from_mapstate(url: str) -> tuple[float, float] | None:
    """Parse coordinates from URL fragment mapstate parameter."""
    try:
        parsed = urlparse(url)
        fragment = parsed.fragment
        
        # Robust handling for #mapstate= vs #?mapstate=
        # We just look for the substring "mapstate=" and take everything after it
        if "mapstate=" in fragment:
            # simple split to handle both cases efficiently
            value_str = fragment.split("mapstate=")[1]
            # If there are other params after, we might need more complex parsing, 
            # but usually mapstate is the main one or we can trust comma separation.
            # mapstate value format: lat,lon,zoom,... 
            
            parts = value_str.split(",")
            if len(parts) >= 2:
                lat = float(parts[0])
                lon = float(parts[1])
                return lat, lon
                
    except (ValueError, IndexError) as e:
        _LOGGER.debug(f"Failed to parse mapstate from {url}: {e}")
        
    return None


def _from_html(html: str) -> tuple[float, float] | None:
    """Parse coordinates from HTML content looking for destination=lat,lon."""
    # Regex for destination=lat,lng (handles both comma and url-encoded comma)
    # destination=46.043011%2C6.767044 or destination=46.043011,6.767044
    pattern = r"destination=([0-9.\-]+)(?:%2C|,)([0-9.\-]+)"
    
    try:
        match = re.search(pattern, html)
        if match:
            lat = float(match.group(1))
            lon = float(match.group(2))
            return lat, lon
    except (ValueError, IndexError) as e:
        _LOGGER.debug(f"Failed to parse coords from HTML: {e}")
        
    return None
