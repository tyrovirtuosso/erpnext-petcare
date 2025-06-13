import frappe
import requests
import json
import os
from petcare.utils.helpers import extract_coordinates_from_url

SITE_CONFIG_PATH = "/home/frappe-user/frappe-bench/sites/erp.masterpet.co.in/site_config.json"

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
        print(f"\nGeocoding {location_name}")
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
    except requests.exceptions.RequestException as e:
        print(f"Network error during geocoding: {str(e)}")
        return None
    except Exception as e:
        print(f"Unexpected error during geocoding: {str(e)}")
        return None

def is_short_url(url):
    return "maps.app.goo.gl" in url

def is_google_maps_url(url):
    return "maps.app.goo.gl" in url or "google.com/maps" in url

def expand_short_url(short_url):
    """Expand a shortened Google Maps URL to its full form"""
    try:
        response = requests.head(short_url, allow_redirects=True)
        return response.url
    except requests.exceptions.RequestException as e:
        print(f"Error expanding short URL: {str(e)}")
        return short_url
    except Exception as e:
        print(f"Unexpected error expanding URL: {str(e)}")
        return short_url

def process_maps_url(url, api_key=None):
    """Process any maps URL or location name and return coordinates"""
    print(f"\nProcessing input: {url}")
    
    # If it's not a URL, treat it as a location name
    if not is_google_maps_url(url):
        print("Detected location name, using geocoding...")
        if not api_key:
            print("Error: Google Maps API key not available")
            return url
            
        coordinates = geocode_location(url, api_key)
        if coordinates:
            print(f"Successfully geocoded location to: {coordinates}")
            return f"https://www.google.com/maps/place/{url}/@{coordinates}"
        return url
        
    if is_short_url(url):
        print("Detected short URL, expanding...")
        url = expand_short_url(url)
        print(f"Expanded URL: {url}")
    else:
        print("Detected long URL, using as is...")
    
    return url

def test_coordinate_extraction():
    """Test coordinate extraction from various input types"""
    # Get API key from site config
    api_key = get_api_key()
    if not api_key:
        print("\nError: Could not retrieve Google Maps API key")
        return []
    
    print(f"\nAPI Key retrieved successfully")
    
    # Test cases - mix of URLs and location names
    test_inputs = [
        "https://maps.app.goo.gl/YNScQ17WJQrZT3Tr5",  # Short URL
        "Chotanikkara",  # Location name
        "https://www.google.com/maps/place/KN-57,+Cross+Road-5,+Keerthi+Nagar,+Mamangalam,+Elamakkara,+Kochi,+Ernakulam,+Kerala+682026/data=!4m6!3m5!1s0x3b080d0b4c975259:0x70784941616ae547!7e2!8m2!3d10.013035499999999!4d76.2943638",  # Long URL
        "Nedumbasery, Athani"  # Location name
    ]
    
    results = []
    for input_data in test_inputs:
        try:
            processed_url = process_maps_url(input_data, api_key)
            coordinates = extract_coordinates_from_url(processed_url)
            
            status = "Success" if coordinates else "Failed"
            result = {
                'input': input_data,
                'coordinates': coordinates,
                'status': status
            }
            
            print(f"\nResult for: {input_data}")
            print(f"Status: {status}")
            print(f"Coordinates: {coordinates if coordinates else 'Not found'}")
            
            results.append(result)
            
        except Exception as e:
            print(f"\nError processing {input_data}: {str(e)}")
            results.append({
                'input': input_data,
                'coordinates': None,
                'status': 'Error',
                'error': str(e)
            })
    
    # Summary
    print("\nSummary:")
    print("-" * 50)
    successful = sum(1 for r in results if r['status'] == 'Success')
    print(f"Successfully processed: {successful}/{len(results)}")
    
    return results

if __name__ == "__main__":
    test_coordinate_extraction() 