import frappe
from frappe import _
import json
import logging
import os
import traceback

# Set up direct file logging with more detailed format
log_file = os.path.join(frappe.get_site_path(), 'logs', 'petcare.log')
logging.basicConfig(
    filename=log_file,
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)

# Initialize logger
logger = logging.getLogger('petcare')

# Test logging with more context
logger.info("=== Petcare Logger Initialized ===")
logger.debug("Debug test message - Logger ready for debugging")
logger.info("Info test message - Logger ready for information tracking")
logger.warning("Warning test message - Logger ready for warnings")
logger.error("Error test message - Logger ready for error tracking")

def check_permission():
    """Check if user has Driver role"""
    user = frappe.session.user
    roles = frappe.get_roles()
    logger.debug(f"Checking permissions for user: {user} with roles: {roles}")
    
    if "Driver" not in roles:
        logger.error(f"Permission denied: User {user} does not have Driver role. Available roles: {roles}")
        frappe.throw(_("You need Driver role to access this page"), frappe.PermissionError)
    logger.info(f"Permission check passed for user {user}")

@frappe.whitelist(allow_guest=True)
def get_grooming_requests(date=None):
    """Get grooming service requests assigned to the logged-in driver, with missing fields info"""
    try:
        check_permission()
        if not date:
            date = frappe.utils.nowdate()
        
        logger.info(f"Fetching grooming requests for date: {date}")
        
        requests = frappe.get_all(
            "Service Request",
            filters={
                "scheduled_date": date,
                "status": "Scheduled"
            },
            fields=[
                "name", "customer", "customer_name", "scheduled_date", "scheduled_date_start", "status", "driver_suggestions", "total_pets",
                "google_maps_link", "territory", "electricity", "water", "living_space", "living_space_notes", "mobile",
                "user_notes", "parking", "service_notes", "amount_after_discount", "discount_amount", "total_amount"
            ]
        )
        
        logger.info(f"Found {len(requests)} grooming requests for date {date}")
        
        for req in requests:
            # Format scheduled_date_start as DD-MM-YYYY HH:MM:SS
            sds = req.get("scheduled_date_start")
            if sds:
                try:
                    if isinstance(sds, str):
                        dt = frappe.utils.get_datetime(sds)
                    else:
                        dt = sds
                    req["scheduled_date_start"] = dt.strftime("%d-%m-%Y %H:%M:%S")
                except Exception as e:
                    logger.error(f"Error formatting date for request {req.get('name')}: {str(e)}")
            # Get current parking value from Customer
            try:
                customer = frappe.get_doc("Customer", req["customer"])
                req["current_parking"] = customer.get("custom_parking")
            except Exception as e:
                logger.error(f"Error fetching customer data for request {req.get('name')}: {str(e)}")
                req["current_parking"] = None
            # Parse driver_suggestions JSON if present (but do not handle pet photos here)
            suggestions = req.get("driver_suggestions")
            if suggestions:
                try:
                    req["driver_suggestions"] = json.loads(suggestions)
                except Exception as e:
                    logger.error(f"Error parsing driver suggestions for request {req.get('name')}: {str(e)}")
                    req["driver_suggestions"] = {}
            else:
                req["driver_suggestions"] = {}
            # Fetch service items child table
            try:
                req["service_items"] = frappe.get_all(
                    "Service Items Child Table",
                    filters={"parent": req["name"]},
                    fields=[
                        "item_code", "item_name", "quantity", "rate", "amount",
                        "pet", "pet_name", "pet_breed", "pet_gender", "pet_behaviour", "pet_age", "pet_notes", "birthday"
                    ]
                )
            except Exception as e:
                logger.error(f"Error fetching service items for request {req.get('name')}: {str(e)}", exc_info=True)
                req["service_items"] = []
            # Fetch pet photos from child table (use correct DocType name)
            try:
                req["pet_photos"] = frappe.get_all(
                    "Pet Photo",
                    filters={"parent": req["name"]},
                    fields=["pet", "image", "service_request"]
                )
            except Exception as e:
                logger.error(f"Error fetching pet photos for request {req.get('name')}: {str(e)}", exc_info=True)
                req["pet_photos"] = []
        return requests
    except Exception as e:
        logger.error(f"Error in get_grooming_requests: {str(e)}", exc_info=True)
        frappe.throw(str(e))

@frappe.whitelist()
def save_driver_draft(service_request_id, grooming_cost=None, payment_method=None, notes=None):
    """Save draft data for a service request (not final submission)"""
    try:
        check_permission()
        doc = frappe.get_doc("Service Request", service_request_id)
        # Save draft fields in custom fields or a child table as per your model
        doc.db_set("driver_grooming_cost", grooming_cost, update_modified=False)
        doc.db_set("driver_payment_method", payment_method, update_modified=False)
        doc.db_set("driver_notes", notes, update_modified=False)
        
        logger.info(f"Saved driver draft for request {service_request_id}")
        return {"status": "draft_saved"}
    except Exception as e:
        logger.error(f"Error saving driver draft for request {service_request_id}: {str(e)}")
        frappe.throw(str(e))

@frappe.whitelist(allow_guest=True)
def save_driver_suggestion(service_request_id, driver_suggestions=None):
    try:
        check_permission()
        doc = frappe.get_doc("Service Request", service_request_id)
        # Store the entire suggestions JSON in the driver_suggestions field
        if driver_suggestions:
            try:
                suggestions = json.loads(driver_suggestions)
                doc.db_set("driver_suggestions", json.dumps(suggestions), update_modified=False)
                logger.info(f"Saved driver suggestions for request {service_request_id}")
            except Exception as e:
                logger.error(f"Error parsing driver suggestions for request {service_request_id}: {str(e)}")
                frappe.throw(str(e))
        return {"status": "suggestion_saved"}
    except Exception as e:
        logger.error(f"Error in save_driver_suggestion for request {service_request_id}: {str(e)}")
        frappe.throw(str(e))

@frappe.whitelist(allow_guest=True)
def get_grooming_request(service_request_id):
    """Get a single grooming service request by ID, with pet photos from child table"""
    try:
        check_permission()
        doc = frappe.get_doc("Service Request", service_request_id)
        data = doc.as_dict()
        # Parse driver_suggestions JSON if present (but do not handle pet photos here)
        suggestions = data.get("driver_suggestions")
        if suggestions:
            try:
                data["driver_suggestions"] = json.loads(suggestions)
            except Exception as e:
                logger.error(f"Error parsing driver suggestions for request {service_request_id}: {str(e)}")
                data["driver_suggestions"] = {}
        else:
            data["driver_suggestions"] = {}
        # Fetch service items
        try:
            data["service_items"] = frappe.get_all(
                "Service Items Child Table",
                filters={"parent": service_request_id},
                fields=[
                    "item_code", "item_name", "quantity", "rate", "amount",
                    "pet", "pet_name", "pet_breed", "pet_gender", "pet_behaviour", "pet_age", "pet_notes", "birthday"
                ]
            )
        except Exception as e:
            logger.error(f"Error fetching service items for request {service_request_id}: {str(e)}", exc_info=True)
            data["service_items"] = []
        # Fetch pet photos from child table (use correct DocType name)
        try:
            data["pet_photos"] = frappe.get_all(
                "Pet Photo",
                filters={"parent": service_request_id},
                fields=["pet", "image", "service_request"]
            )
        except Exception as e:
            logger.error(f"Error fetching pet photos for request {service_request_id}: {str(e)}", exc_info=True)
            data["pet_photos"] = []
        return data
    except Exception as e:
        logger.error(f"Error in get_grooming_request for request {service_request_id}: {str(e)}", exc_info=True)
        frappe.throw(str(e))

@frappe.whitelist()
def delete_pet_photo(service_request_id, photo_row_id):
    """Delete a pet photo row from the pet_photos child table in Service Request."""
    try:
        logger.info(f"Starting photo deletion process - Service Request: {service_request_id}, Photo Row: {photo_row_id}")
        check_permission()
        
        if not service_request_id or not photo_row_id:
            logger.error(f"Missing required parameters - Service Request ID: {service_request_id}, Photo Row ID: {photo_row_id}")
            return {"status": "error", "message": "Missing required parameters"}
            
        doc = frappe.get_doc("Service Request", service_request_id)
        logger.debug(f"Retrieved Service Request document: {service_request_id}")
        
        # Find and remove the child row
        to_remove = None
        for row in doc.pet_photos:
            if row.name == photo_row_id:
                to_remove = row
                logger.debug(f"Found photo row to delete: {photo_row_id}")
                break
                
        if to_remove:
            # Get the file URL before removing
            file_url = to_remove.image
            logger.debug(f"Photo file URL: {file_url}")
            
            doc.remove(to_remove)
            doc.save()
            frappe.db.commit()
            logger.info(f"Successfully removed photo row from Service Request: {service_request_id}")
            
            # Try to delete the actual file if it exists
            try:
                if file_url:
                    file_name = file_url.split('/')[-1]
                    logger.debug(f"Attempting to delete file: {file_name}")
                    frappe.delete_doc('File', file_name)
                    logger.info(f"Successfully deleted file: {file_name}")
            except Exception as e:
                logger.warning(f"Could not delete file {file_name}: {str(e)}\n{traceback.format_exc()}")
            
            logger.info(f"Photo deletion completed successfully - Service Request: {service_request_id}, Photo Row: {photo_row_id}")
            return {"status": "success"}
        else:
            logger.error(f"Photo row not found - Service Request: {service_request_id}, Photo Row: {photo_row_id}")
            return {"status": "error", "message": "Photo not found"}
            
    except Exception as e:
        error_msg = f"Error deleting pet photo - Service Request: {service_request_id}, Photo Row: {photo_row_id}\nError: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def upload_images_to_pet_photos(service_request_id, pet_id, image_urls):
    """Upload images to the pet_photos child table in the Service Request doctype."""
    try:
        logger.info(f"Starting image upload process - Service Request: {service_request_id}, Pet: {pet_id}")
        logger.debug(f"Image URLs to upload: {image_urls}")

        check_permission()
        doc = frappe.get_doc("Service Request", service_request_id)
        logger.debug(f"Retrieved Service Request document: {service_request_id}")

        # Ensure image_urls is a list
        if isinstance(image_urls, str):
            image_urls = [image_urls]
            logger.debug(f"Converted image_urls string to list: {image_urls}")

        for image_url in image_urls:
            file_name = image_url.split('/')[-1]
            logger.info(f"Processing image: {file_name}")
            try:
                doc.append("pet_photos", {
                    "pet": pet_id,
                    "image": image_url,
                    "service_request": service_request_id
                })
                logger.debug(f"Appended image to pet_photos - Pet: {pet_id}, Image: {file_name}")
            except Exception as e:
                logger.error(f"Error appending photo to pet_photos table: {str(e)}\n{traceback.format_exc()}")
                raise

        try:
            doc.save()
            frappe.db.commit()
            logger.info(f"Successfully saved Service Request {service_request_id} with new pet photos")
        except Exception as e:
            logger.error(f"Error saving Service Request {service_request_id}: {str(e)}\n{traceback.format_exc()}")
            raise

        return {"status": "success"}

    except Exception as e:
        error_msg = f"Error in upload_images_to_pet_photos - Service Request: {service_request_id}, Pet: {pet_id}\nError: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        return {"status": "error", "message": str(e)}

def get_context(context):
    context.no_cache = 1 