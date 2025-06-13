import re
import requests
from urllib.parse import urlparse, parse_qs, unquote
import frappe
from frappe import _
import json

def extract_coordinates_from_url(url: str) -> str:
    """
    Extract coordinates from various Google Maps URL formats.
    Handles:
    - Full URLs with @lat,lng
    - URLs with ?q=lat,lng
    - Short URLs (goo.gl)
    - Place IDs
    - Embedded map URLs
    
    Args:
        url (str): Google Maps URL
        
    Returns:
        str: Coordinates in "lat,lng" format or None if not found
    """
    if not url:
        return None
        
    try:
        # Setup session with proper headers to avoid blocks
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

        # Handle short URLs first
        if 'goo.gl' in url:
            try:
                # Use GET instead of HEAD to get the actual page content
                response = session.get(url, timeout=10)
                url = response.url
                # If we got redirected to a consent page, try to extract the real URL
                if 'consent.google.com' in url:
                    continue_url = parse_qs(urlparse(url).query).get('continue', [None])[0]
                    if continue_url:
                        url = unquote(continue_url)
            except Exception as e:
                frappe.log_error(f"Error resolving short URL: {str(e)}")
                return None

        # Extract coordinates using various patterns
        coordinates = None
        
        # Pattern 1: @lat,lng with optional zoom and other parameters
        pattern1 = r'@(-?\d+\.?\d*),(-?\d+\.?\d*)(?:,\d+\.?\d*)?z?'
        match = re.search(pattern1, url)
        if match:
            lat, lng = match.groups()
            coordinates = f"{lat},{lng}"
            
        # Pattern 2: ?q=lat,lng or ?query=lat,lng
        if not coordinates:
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            
            # Check various query parameters
            for param in ['q', 'query', 'center']:
                if param in query_params:
                    value = query_params[param][0]
                    # Handle both comma-separated and space-separated coordinates
                    coord_match = re.search(r'(-?\d+\.?\d*)[,\s]+(-?\d+\.?\d*)', value)
                    if coord_match:
                        lat, lng = coord_match.groups()
                        coordinates = f"{lat},{lng}"
                        break

        # Pattern 3: Embedded maps with various formats
        if not coordinates:
            # Format 1: !2d and !3d
            pattern3a = r'!2d(-?\d+\.?\d*)!3d(-?\d+\.?\d*)'
            match = re.search(pattern3a, url)
            if match:
                lng, lat = match.groups()
                coordinates = f"{lat},{lng}"
            else:
                # Format 2: data=!3m1!4b1!4m5!3m4!1m2!1d{lng}!2d{lat}
                pattern3b = r'!1d(-?\d+\.?\d*)!2d(-?\d+\.?\d*)'
                match = re.search(pattern3b, url)
                if match:
                    lng, lat = match.groups()
                    coordinates = f"{lat},{lng}"

        # Pattern 4: Place ID
        if not coordinates and ('place_id:' in url or 'place/' in url):
            try:
                # Try both formats of place ID
                place_id_match = re.search(r'place(?:/|\?q=place_id:)([\w\-]+)', url)
                if place_id_match:
                    place_id = place_id_match.group(1)
                    api_key = frappe.get_value('Google Settings', None, 'api_key')
                    
                    if api_key:
                        place_details_url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=geometry&key={api_key}"
                        response = session.get(place_details_url)
                        data = response.json()
                        
                        if data.get('result') and data['result'].get('geometry'):
                            location = data['result']['geometry']['location']
                            coordinates = f"{location['lat']},{location['lng']}"
            except Exception as e:
                frappe.log_error(f"Error fetching place details: {str(e)}")

        # Validate coordinates
        if coordinates:
            try:
                lat, lng = map(float, coordinates.split(','))
                if -90 <= lat <= 90 and -180 <= lng <= 180:
                    return coordinates
            except (ValueError, TypeError):
                pass

        # If no coordinates found, try to extract from the page content for short URLs
        if not coordinates and 'goo.gl' in url:
            try:
                response = session.get(url)
                content = response.text
                # Look for coordinates in the page content
                coord_match = re.search(r'window\.APP_INITIALIZATION_STATE=\[.*?(-?\d+\.\d+),(-?\d+\.\d+)', content)
                if coord_match:
                    lat, lng = coord_match.groups()
                    coordinates = f"{lat},{lng}"
                    if is_valid_coordinates(coordinates):
                        return coordinates
            except Exception as e:
                frappe.log_error(f"Error extracting coordinates from page content: {str(e)}")

        return None

    except Exception as e:
        frappe.log_error(f"Error extracting coordinates: {str(e)}")
        return None

def is_valid_coordinates(coordinates: str) -> bool:
    """
    Validate if coordinates string is in correct format and range.
    
    Args:
        coordinates (str): String in "lat,lng" format
        
    Returns:
        bool: True if coordinates are valid
    """
    if not coordinates or not isinstance(coordinates, str):
        return False
        
    try:
        lat, lng = map(float, coordinates.split(','))
        return -90 <= lat <= 90 and -180 <= lng <= 180
    except (ValueError, TypeError):
        return False 