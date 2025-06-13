import re
import requests
from .config import get_google_maps_api_key
import frappe
import json
import urllib.parse

def extract_coordinates_from_url(location):
    """
    Extract coordinates from a Google Maps URL using multiple methods:
    1. Direct URL parsing
    2. Google Maps API for short URLs
    """
    if not isinstance(location, str):
        return None

    print(f"Processing location: {location}")  # Debug log
    
    # Method 1: Try direct coordinate extraction from URL
    def extract_from_url(url):
        patterns = [
            r"@(-?\d+\.?\d*),(-?\d+\.?\d*)",  # Pattern for @lat,lng
            r"!3d(-?\d+\.?\d*)!4d(-?\d+\.?\d*)",  # Pattern for !3d{lat}!4d{lng}
            r"ll=(-?\d+\.?\d*),(-?\d+\.?\d*)",  # Pattern for ll=lat,lng
            r"q=(-?\d+\.?\d*),(-?\d+\.?\d*)"  # Pattern for q=lat,lng
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                lat, lng = match.group(1), match.group(2)
                return f"{lat},{lng}"
        return None

    # For short URLs, try Google Maps API directly
    if "goo.gl" in location or "maps.app.goo.gl" in location:
        try:
            # Extract the ID from the short URL
            url_parts = location.split('/')
            place_ref = url_parts[-1]
            
            api_key = get_google_maps_api_key()
            if not api_key:
                print("No Google Maps API key found")  # Debug log
                return None
            
            # Try using Place Details API with the reference
            places_url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_ref}&fields=geometry&key={api_key}"
            places_response = requests.get(places_url)
            places_data = places_response.json()
            
            if places_data.get('result', {}).get('geometry', {}).get('location'):
                location_data = places_data['result']['geometry']['location']
                return f"{location_data['lat']},{location_data['lng']}"
                
            # If that fails, try Geocoding API
            geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json?place_id={place_ref}&key={api_key}"
            geocode_response = requests.get(geocode_url)
            geocode_data = geocode_response.json()
            
            if geocode_data.get('results') and geocode_data['results'][0].get('geometry', {}).get('location'):
                location_data = geocode_data['results'][0]['geometry']['location']
                return f"{location_data['lat']},{location_data['lng']}"
                
        except Exception as e:
            print(f"Error using Google Maps API: {e}")  # Debug log
            
            # Fallback: Try to use the Maps Embed API to get the iframe
            try:
                embed_url = f"https://www.google.com/maps/embed/v1/place?key={api_key}&q=place_id:{place_ref}"
                response = requests.get(embed_url)
                
                # Look for coordinates in the response
                coords = extract_from_url(response.text)
                if coords:
                    return coords
            except Exception as e:
                print(f"Error using Maps Embed API: {e}")  # Debug log
    
    # Try direct extraction for full URLs
    coords = extract_from_url(location)
    if coords:
        return coords
        
    print("No coordinates found using any method")  # Debug log
    return None
