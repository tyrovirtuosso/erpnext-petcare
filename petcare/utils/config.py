from frappe import get_site_config

def get_google_maps_api_key():
    return get_site_config().get("google_maps_api_key")
