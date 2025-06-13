from petcare.utils.directions import calculate_round_trip, calculate_bearings_from_center
from petcare.utils.helpers import extract_coordinates_from_url
from petcare.utils.config import get_google_maps_api_key
import frappe
from frappe.utils import nowdate, getdate
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice
import math

# Set up logger
frappe.utils.logger.set_log_level("DEBUG")
logger = frappe.logger("service_request_api", allow_site=True, file_count=50)

@frappe.whitelist()
def calculate_service_distance(service_request_name):
    try:
        
        # Log API access
        user = frappe.session.user
        logger.info(f"{user} accessed calculate_service_distance for {service_request_name}")
        doc = frappe.get_doc("Service Request", service_request_name)
        api_key = get_google_maps_api_key()
        
        
        customer_location = extract_coordinates_from_url(doc.google_maps_link)
        truck_location = extract_coordinates_from_url(doc.assigned_truckstore_google_map_location)
        print(f"Customer Location: {customer_location}")
        print(f"Truck Location: {truck_location}")
        # Log input data
        logger.debug(f"Customer Locationn: {customer_location}")
        logger.debug(f"Truck Location: {truck_location}")

        if not customer_location or not truck_location:
            logger.error("Both customer and truck/store locations must be provided.")
            frappe.throw("Both customer and truck/store locations must be provided.")
        
        # Calculate round trip distance
        locations = [truck_location, customer_location, truck_location]
        result = calculate_round_trip(api_key, locations)
        
        # Log calculation results
        logger.debug(f"API Result: {result}")
        
        result = calculate_round_trip(api_key, locations)
        
        # Calculate bearings and directions
        bearings = calculate_bearings_from_center(api_key, truck_location, [customer_location])
        logger.debug(f"Bearings: {bearings}")
        
        # Extract only the direction
        direction = bearings[0]["direction"] if bearings else None
        
        # Log extracted direction
        logger.debug(f"Extracted Direction: {direction}")

        if direction:
            direction = direction.strip()
        
        logger.debug(f"Extracted Direction no quotes: {direction}")
        
        # Fetch cost per km and free km limit
        cost_per_km = frappe.db.get_single_value("Petcare Settings", "cost_per_km")
        free_distance_threshold_km = frappe.db.get_single_value("Petcare Settings", "free_distance_threshold_km")
        logger.debug(f"Cost Per KM: {cost_per_km}")
        logger.debug(f"Free KM Limit: {free_distance_threshold_km}")

        if not cost_per_km or not free_distance_threshold_km:
            frappe.throw("Cost Per KM or Free KM Limit is not defined in Petcare Settings.")

        # Calculate total distance in KM
        total_travel_kms = result["total_distance_meters"] / 1000
        logger.debug(f"Total Travel KMs: {total_travel_kms}")
        # Calculate traveling cost based on the free distance threshold
        chargeable_kms = round(max(0, total_travel_kms - free_distance_threshold_km),0)  # KMs above the free limit
        # Calculate the traveling cost
        traveling_cost = chargeable_kms * cost_per_km

        # Round the traveling cost to the nearest upper multiple of 50
        traveling_cost = math.ceil(traveling_cost / 50) * 50
        
        # Round total travel duration (no decimals)
        total_duration_minutes = round(result["total_duration_seconds"] / 60)
        
        logger.debug(f"Chargeable KMs: {chargeable_kms}")
        logger.debug(f"Traveling Cost: {traveling_cost}")
        
        # Add 18% GST to traveling cost
        traveling_cost_after_GST = traveling_cost * 1.18
        logger.debug(f"Traveling Cost After GST: {traveling_cost_after_GST}")

        # Round traveling cost after GST to the nearest 50
        final_traveling_cost = math.ceil(traveling_cost_after_GST / 50) * 50
        logger.debug(f"Final Traveling Cost (Rounded to 50): {final_traveling_cost}")
        
        # Format the duration into hours and minutes
        hours = total_duration_minutes // 60
        minutes = total_duration_minutes % 60
        duration_hours_and_minutes = f"{hours} hour{'s' if hours != 1 else ''} and {minutes} minute{'s' if minutes != 1 else ''}"
        
        return {
            "distance_km": result["total_distance_meters"] / 1000,
            "duration_minutes": total_duration_minutes,
            "duration_hours_and_minutes": duration_hours_and_minutes,  
            "direction": direction,
            "traveling_cost": traveling_cost,
            "chargeable_kms": chargeable_kms,
            "traveling_cost_after_GST": traveling_cost_after_GST,
            "final_traveling_cost": final_traveling_cost
        }

    except Exception as e:
        logger.exception(f"Error in calculate_service_distance: {e}")
        frappe.log_error(frappe.get_traceback(), "Service Distance Calculation Error")
        raise e


