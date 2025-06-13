import frappe
from frappe import _
import requests
import json
import os

SITE_CONFIG_PATH = "/home/frappe-user/frappe-bench/sites/erp.masterpet.co.in/site_config.json"

def has_petcare_access():
    """Check if user has Petcare or System Manager role"""
    roles = frappe.get_roles(frappe.session.user)
    return "System Manager" in roles or "Petcare" in roles

@frappe.whitelist()
def get_google_maps_api_key():
    """Get Google Maps API key from site config for frontend use"""
    if not has_petcare_access():
        frappe.throw(_("Access denied. You need Petcare role to access this feature."))
        
    try:
        if os.path.exists(SITE_CONFIG_PATH):
            with open(SITE_CONFIG_PATH) as f:
                site_config = json.load(f)
                api_key = site_config.get("google_maps_api_key")
                if api_key:
                    return api_key
        print(f"Error: Could not find API key in {SITE_CONFIG_PATH}")
        return None
    except Exception as e:
        print(f"Error reading site config: {str(e)}")
        return None

def get_api_key():
    """Get Google Maps API key from site config"""
    try:
        if os.path.exists(SITE_CONFIG_PATH):
            with open(SITE_CONFIG_PATH) as f:
                site_config = json.load(f)
                api_key = site_config.get("google_maps_api_key")
                if api_key:
                    return api_key
        print(f"Error: Could not find API key in {SITE_CONFIG_PATH}")
        return None
    except Exception as e:
        print(f"Error reading site config: {str(e)}")
        return None

def geocode_location(location_name, api_key):
    """Convert a location name to coordinates using Google Maps Geocoding API"""
    try:
        base_url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            "address": location_name,
            "key": api_key
        }
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        
        data = response.json()
        if data["status"] == "OK" and data["results"]:
            location = data["results"][0]["geometry"]["location"]
            return f"{location['lat']},{location['lng']}"
        else:
            print(f"Geocoding error: {data.get('status', 'Unknown error')}")
            if data.get("error_message"):
                print(f"Error details: {data['error_message']}")
            return None
    except Exception as e:
        print(f"Error during geocoding: {str(e)}")
        return None

def is_short_url(url):
    """Check if URL is a shortened Google Maps URL"""
    return "goo.gl/maps" in url or "maps.app.goo.gl" in url

def is_google_maps_url(url):
    """Check if URL is any form of Google Maps URL"""
    return "goo.gl/maps" in url or "maps.app.goo.gl" in url or "google.com/maps" in url

def expand_short_url(short_url):
    """Expand a shortened Google Maps URL to its full form"""
    try:
        # Add protocol if missing
        if not short_url.startswith('http'):
            short_url = 'https://' + short_url
            
        print(f"Attempting to expand URL: {short_url}")
        session = requests.Session()
        response = session.head(short_url, allow_redirects=True)
        final_url = response.url
        print(f"Final URL after expansion: {final_url}")
        return final_url
    except Exception as e:
        print(f"Error expanding URL: {str(e)}")
        return short_url

def extract_coordinates_from_url(url):
    """Extract coordinates from a Google Maps URL or geocode a location name"""
    if not url:
        return None
        
    api_key = get_api_key()
    
    # Clean up URL
    url = url.strip()
    if not url.startswith('http'):
        url = 'https://' + url
    
    print(f"Processing URL: {url}")
    
    # If it's not a URL, treat it as a location name
    if not is_google_maps_url(url):
        if not api_key:
            print(f"Error: Google Maps API key not available for geocoding {url}")
            return None
        return geocode_location(url, api_key)
        
    # Handle short URLs
    if is_short_url(url):
        print(f"Expanding short URL: {url}")
        expanded_url = expand_short_url(url)
        print(f"Expanded URL: {expanded_url}")
        url = expanded_url
    
    # Extract coordinates from URL
    try:
        # Look for coordinates in various URL formats
        import re
        
        # Try q=lat,lng format (common in expanded short URLs)
        coord_match = re.search(r'[?&]q=(-?\d+\.?\d*),(-?\d+\.?\d*)', url)
        if coord_match:
            lat, lng = coord_match.groups()
            print(f"Found coordinates in q parameter: {lat},{lng}")
            return f"{lat},{lng}"
        
        # Try @lat,lng format
        coord_match = re.search(r'@(-?\d+\.?\d*),(-?\d+\.?\d*)', url)
        if coord_match:
            lat, lng = coord_match.groups()
            print(f"Found coordinates in @ format: {lat},{lng}")
            return f"{lat},{lng}"
            
        # Try !3d!4d format
        coord_match = re.search(r'!3d(-?\d+\.?\d*)!4d(-?\d+\.?\d*)', url)
        if coord_match:
            lat, lng = coord_match.groups()
            print(f"Found coordinates in !3d!4d format: {lat},{lng}")
            return f"{lat},{lng}"
            
        # Try place/ format with coordinates
        coord_match = re.search(r'place/[^/]+/@(-?\d+\.?\d*),(-?\d+\.?\d*)', url)
        if coord_match:
            lat, lng = coord_match.groups()
            print(f"Found coordinates in place format: {lat},{lng}")
            return f"{lat},{lng}"
            
        # Try data=format with coordinates
        coord_match = re.search(r'data=.*!8m2!3d(-?\d+\.?\d*)!4d(-?\d+\.?\d*)', url)
        if coord_match:
            lat, lng = coord_match.groups()
            print(f"Found coordinates in data format: {lat},{lng}")
            return f"{lat},{lng}"
            
        # Try maps/place format
        coord_match = re.search(r'maps/place/[^/]+/(-?\d+\.?\d*),(-?\d+\.?\d*)', url)
        if coord_match:
            lat, lng = coord_match.groups()
            print(f"Found coordinates in maps/place format: {lat},{lng}")
            return f"{lat},{lng}"
        
        print("No coordinates found in URL patterns, trying location extraction...")
        
        # If no coordinates found in URL, try to extract location name and geocode
        if api_key:
            # Try to extract location from the URL
            location_match = re.search(r'place/([^/@]+)', url)
            if location_match:
                location_name = location_match.group(1).replace('+', ' ')
                print(f"Extracted location name from URL: {location_name}")
                return geocode_location(location_name, api_key)
            
            # If all else fails, try geocoding the entire URL
            print("No location name found, trying to geocode the URL...")
            return geocode_location(url, api_key)
            
        return None
    except Exception as e:
        print(f"Error extracting coordinates: {str(e)}")
        return None

@frappe.whitelist()
def get_customer_locations(lead_statuses=None):
    """
    Get locations of customers that have valid coordinates, filtered by lead status if specified
    """
    if not has_petcare_access():
        frappe.throw(_("Access denied. You need Petcare role to access this feature."))
        
    try:
        filters = {
            "custom_latitude": ["!=", "0.000"],
            "custom_longitude": ["!=", "0.000"]
        }
        
        # Add lead status filter if specified
        if lead_statuses:
            lead_status_list = json.loads(lead_statuses)
            if lead_status_list:
                filters["custom_lead_status"] = ["in", lead_status_list]

        customers = frappe.get_all(
            "Customer",
            filters=filters,
            fields=[
                "name", "customer_name", "mobile_no", "territory",
                "custom_latitude as latitude", "custom_longitude as longitude",
                "custom_days_since_last_service", "custom_total_pets",
                "custom_living_space", "custom_parking", "custom_electricity",
                "custom_water_", "custom_lead_status"
            ]
        )

        return {
            "customers": customers,
            "failed": []
        }
        
    except Exception as e:
        frappe.log_error(f"Error in get_customer_locations: {str(e)}")
        return {
            "customers": [],
            "failed": [],
            "error": str(e)
        } 