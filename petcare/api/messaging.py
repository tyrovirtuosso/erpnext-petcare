import frappe
from typing import Dict, List, Optional
from datetime import datetime

# Constants
DEFAULT_NOT_PROVIDED = "Not Provided"
DEFAULT_NA = "N/A"
DEFAULT_NO_LINK = "No link provided"

def format_boolean_field(value: Optional[str]) -> str:
    """Format boolean-like fields to Yes/No."""
    return "Yes" if value and value.lower() in ["yes", "available"] else "No"

def format_currency(amount: Optional[float]) -> str:
    """Format amount to currency string."""
    return f"₹{amount:.2f}" if amount else DEFAULT_NA

def format_date(date: Optional[datetime]) -> str:
    """Format date to string."""
    return date.strftime("%d-%m-%Y") if date else "Not Scheduled"

def format_time(date: Optional[datetime]) -> str:
    """Format time to string."""
    return date.strftime("%I:%M %p") if date else "Not Scheduled"

def format_service_item(item: Dict) -> str:
    """Format a single service item with all its details."""
    pet_info = f"{item.pet_name}" if item.pet_name else "Unnamed Pet"
    if item.pet_gender:
        pet_info += f" ({item.pet_gender})"
    
    # Format pet details in a single line
    details = []
    if item.pet_breed:
        details.append(item.pet_breed)
    if item.pet_age:
        details.append(f"{round(float(item.pet_age), 1)} yrs")
    if item.pet_behaviour:
        details.append(item.pet_behaviour)
    
    details_str = ", ".join(details) if details else DEFAULT_NA
    
    return f"• {pet_info} – {details_str}"

def format_service_items(services: Optional[List[Dict]]) -> str:
    """Format all service items into a string."""
    if not services:
        return "No services listed."
    
    # Group items by pet
    pet_groups = {}
    for item in services:
        if item.pet_name not in pet_groups:
            pet_groups[item.pet_name] = []
        pet_groups[item.pet_name].append(item)
    
    # Format the output
    output = []
    for pet_name, items in pet_groups.items():
        # Get pet details from first item
        pet_details = format_service_item(items[0])
        # Remove the bullet point from pet details
        pet_details = pet_details[2:]  # Remove "• " from the start
        
        # Format all services for this pet
        service_texts = []
        for item in items:
            service_texts.append(f"{item.item_name} (₹{item.amount:.2f})")
        
        # Combine pet details with all services
        output.append(f"• {pet_details}, {', '.join(service_texts)}")
    
    return "\n".join(output)

def get_customer_contacts(customer: str) -> List[str]:
    """Fetch all contact numbers for a customer."""
    if not customer:
        return []
    
    # Get all contacts linked to the customer
    contacts = frappe.get_all(
        "Contact",
        filters={"link_doctype": "Customer", "link_name": customer},
        fields=["first_name", "mobile_no", "phone"]
    )
    
    # Filter out None/empty values and format numbers with names
    formatted_contacts = []
    for contact in contacts:
        if contact.mobile_no:
            name = contact.first_name or "Customer"
            formatted_contacts.append(f"{name} ({contact.mobile_no})")
    
    return formatted_contacts

def get_customer_type(customer: str) -> str:
    """Determine if customer is first-time or repeat based on completed service requests."""
    if not customer:
        return "First-Time Customer"
    
    # Get count of completed service requests for the customer
    completed_requests = frappe.db.count(
        "Service Request",
        filters={
            "customer": customer,
            "status": "Completed"
        }
    )
    
    return "Repeat Customer" if completed_requests > 0 else "First-Time Customer"

def extract_service_request_data(service_request_id: str) -> Dict:
    """Extract and format all required data from service request."""
    service_request = frappe.get_doc("Service Request", service_request_id)
    
    # Format living space information
    living_space_info = ""
    if service_request.living_space:
        living_space_info = f"{service_request.living_space}"
        if service_request.living_space_notes:
            living_space_info += f" ({service_request.living_space_notes})"
    
    # Format pricing information
    pricing_info = {
        "total_amount": format_currency(service_request.total_amount),
        "amount_after_discount": format_currency(service_request.amount_after_discount),
        "discount_amount": format_currency(service_request.discount_amount) if service_request.discount_amount else None
    }
    
    # Get all customer contact numbers with names
    customer_contacts = get_customer_contacts(service_request.customer)
    customer_contacts_str = ", ".join(customer_contacts) if customer_contacts else DEFAULT_NOT_PROVIDED
    
    return {
        "customer_name": service_request.customer_name,
        "customer_type": get_customer_type(service_request.customer),
        "scheduled_date": format_date(service_request.scheduled_date),
        "scheduled_time": format_time(service_request.scheduled_date_start),
        "service_type": service_request.service_request_type,
        "google_maps_link": service_request.google_maps_link or DEFAULT_NO_LINK,
        "territory": service_request.territory or DEFAULT_NA,
        "parking": format_boolean_field(service_request.parking),
        "electricity": format_boolean_field(service_request.electricity),
        "water": format_boolean_field(service_request.water),
        "living_space": living_space_info or DEFAULT_NA,
        "mobile": service_request.mobile or DEFAULT_NOT_PROVIDED,
        "customer_contacts": customer_contacts_str,
        "total_pets": service_request.total_pets or DEFAULT_NA,
        "pricing": pricing_info,
        "driver_name": service_request.assigned_driver or "Not Assigned",
        "driver_phone": service_request.driver_phone or DEFAULT_NOT_PROVIDED,
        "service_items": format_service_items(service_request.services),
        "service_notes": service_request.service_notes or DEFAULT_NA,
        "services": service_request.services  # Add raw services data
    }

def generate_customer_message(data: Dict) -> str:
    """Generate the customer confirmation message."""
    # Format pricing section
    if data['pricing']['discount_amount']:
        pricing_section = f"Pets: {data['total_pets']} | Total: {data['pricing']['total_amount']}"
        pricing_section += f"\nDiscount: {data['pricing']['discount_amount']}\nFinal Amount: *{data['pricing']['amount_after_discount']}*"
    else:
        pricing_section = f"Pets: {data['total_pets']} | Total: *{data['pricing']['total_amount']}*"
    
    # Get number of unique pets
    unique_pets = len(set(item.pet_name for item in data.get('services', [])))
    pet_text = "little one" if unique_pets == 1 else "little ones"
    
    return f"""Hi {data['customer_name']} 👋,

Your {data['service_type']} session is confirmed—looking forward to pampering your {pet_text}! 🛁

Date: {data['scheduled_date']}
Time: {data['scheduled_time']}
Location: {data['territory']}
Living Space: {data['living_space']}

Parking: {data['parking']} | Electricity: {data['electricity']} | Water: {data['water']}
{pricing_section}

Grooming Details:
{data['service_items']}

Assigned Driver: {data['driver_name']} ({data['driver_phone']})

If you have any questions before the appointment, feel free to reach out. See you soon!

— Team Masterpet""".strip()

def generate_driver_message(data: Dict) -> str:
    """Generate the driver assignment message."""
    # Format pricing section
    pricing_section = f"""Total Amount: {data['pricing']['total_amount']}"""
    if data['pricing']['discount_amount']:
        pricing_section += f"""
Discount Applied: {data['pricing']['discount_amount']}
Final Amount: *{data['pricing']['amount_after_discount']}*"""
    
    return f"""Customer: {data['customer_name']} ({data['customer_type']})

*Service Notes:*
{data['service_notes']}

Date: {data['scheduled_date']}
Time: {data['scheduled_time']}
Location: {data['territory']}
Google Maps: {data['google_maps_link']}

Living Space: {data['living_space']}
Parking: {data['parking']}
Electricity: {data['electricity']}
Water: {data['water']}

Total Pets: {data['total_pets']}
{pricing_section}

Grooming Details:
{data['service_items']}

Customer Contact Numbers: {data['customer_contacts']}

Please contact the customer before heading to the location.""".strip()

@frappe.whitelist()
def generate_messages(service_request_id: str) -> Dict[str, str]:
    """
    Generates confirmation messages for both the customer and the driver with all relevant details.
    
    Args:
        service_request_id (str): The ID of the service request
        
    Returns:
        Dict[str, str]: Dictionary containing customer and driver messages
    """
    try:
        data = extract_service_request_data(service_request_id)
        return {
            "customer": generate_customer_message(data),
            "driver": generate_driver_message(data)
        }
    except Exception as e:
        frappe.log_error(f"Error generating messages for service request {service_request_id}: {str(e)}")
        return {
            "customer": "Error generating message. Please contact support.",
            "driver": "Error generating message. Please contact support."
        }

@frappe.whitelist()
def get_driver_phone(driver):
    """
    Fetches the phone number of the assigned driver (Contact).
    """
    phone = frappe.db.get_value("Contact", driver, "mobile_no") or frappe.db.get_value("Contact", driver, "phone")
    return phone or "Not Provided"
