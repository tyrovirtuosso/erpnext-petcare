import googlemaps
import math

def get_directions_data(api_key, origin, destination, departure_time='now', mode='driving'):
    gmaps = googlemaps.Client(key=api_key)
    try:
        response = gmaps.directions(
            origin=origin,
            destination=destination,
            mode=mode,
            departure_time=departure_time
        )
        if response:
            leg = response[0]['legs'][0]
            return {
                "distance_meters": leg['distance']['value'],
                "duration_seconds": leg['duration']['value'],
                "duration_in_traffic_seconds": leg.get('duration_in_traffic', {}).get('value', leg['duration']['value'])
            }
        else:
            raise ValueError("No directions found.")
    except Exception as e:
        raise ValueError(f"Error fetching directions: {e}")

def calculate_round_trip(api_key, locations, departure_time='now', mode='driving'):
    total_distance = 0
    total_duration = 0
    total_duration_in_traffic = 0
    for i in range(len(locations) - 1):
        result = get_directions_data(api_key, locations[i], locations[i + 1], departure_time, mode)
        total_distance += result['distance_meters']
        total_duration += result['duration_seconds']
        total_duration_in_traffic += result['duration_in_traffic_seconds']
    return {
        "total_distance_meters": total_distance,
        "total_duration_seconds": total_duration,
        "total_duration_in_traffic_seconds": total_duration_in_traffic
    }

def get_coordinates(api_key, address):
    """
    Get the latitude and longitude for an address using Google Maps Geocoding API.
    """
    gmaps = googlemaps.Client(key=api_key)
    geocode_result = gmaps.geocode(address)
    
    if geocode_result:
        location = geocode_result[0]['geometry']['location']
        return location['lat'], location['lng']
    else:
        raise ValueError(f"Could not geocode address: {address}")
    
    
def calculate_initial_compass_bearing(lat1, lon1, lat2, lon2):
    """
    Calculate the initial compass bearing between two points.
    
    Parameters:
        lat1, lon1: Latitude and longitude of the first point.
        lat2, lon2: Latitude and longitude of the second point.
    
    Returns:
        float: Initial bearing in degrees.
    """
    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)
    
    d_lon = lon2 - lon1
    
    x = math.sin(d_lon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1) * math.cos(lat2) * math.cos(d_lon))
    initial_bearing = math.atan2(x, y)
    initial_bearing = math.degrees(initial_bearing)
    return (initial_bearing + 360) % 360

def get_compass_direction(bearing):
    """
    Convert a bearing in degrees to a human-readable compass direction.
    
    Parameters:
        bearing (float): Bearing in degrees.
    
    Returns:
        str: Compass direction (e.g., "North", "North-East").
    """
    directions = ["North", "North-East", "East", "South-East", 
                  "South", "South-West", "West", "North-West"]
    index = round(bearing / 45) % 8
    return directions[index]

def calculate_bearings_from_center(api_key, central_location, other_locations):
    """
    Calculate the compass bearings from a central location to other locations.

    Parameters:
        api_key (str): Google Maps API key.
        central_location (str): The central location.
        other_locations (list): List of other location strings.

    Returns:
        list: Bearings and compass directions from the central location to each other location.
    """
    bearings = []
    central_lat, central_lng = get_coordinates(api_key, central_location)

    for location in other_locations:
        lat, lng = get_coordinates(api_key, location)
        bearing = calculate_initial_compass_bearing(central_lat, central_lng, lat, lng)
        direction = get_compass_direction(bearing)
        bearings.append({
            "from": central_location,
            "to": location,
            "bearing": round(bearing, 2),
            "direction": direction
        })

    return bearings