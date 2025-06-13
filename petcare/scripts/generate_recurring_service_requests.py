import frappe
from frappe.utils import nowdate, add_days, add_months, getdate

def generate_recurring_service_requests():
    today = getdate(nowdate())

    # Fetch active Service Repeat records
    service_repeats = frappe.get_all("Service Repeat",
        filters={"status": "Active"},
        fields=["name", "customer", "start_date", "recurrence_frequency", "repeat_end_date", 
                "repeat_until_cancelled", "service_request_type",
                "assigned_truckstore", "generation_window_days"]
    )

    for repeat in service_repeats:
        start_date = getdate(repeat.start_date)
        generation_window = repeat.generation_window_days or 30  # Default to 30 days if not set

        # Calculate upcoming service dates within the window
        upcoming_dates = get_upcoming_service_dates(start_date, repeat.recurrence_frequency, today, generation_window)

        for service_date in upcoming_dates:
            # Check if a service request already exists for this customer on this date
            existing_request = frappe.db.exists("Service Request", {
                "customer": repeat.customer,
                "scheduled_date": service_date
            })

            if existing_request:
                continue  # Skip to avoid duplicates

            # Create new Service Request
            new_service_request = frappe.get_doc({
                "doctype": "Service Request",
                "customer": repeat.customer,
                "scheduled_date": service_date,  # ✅ Correctly set dynamically
                "status": "Scheduled",  # Hardcoded
                "source": "Auto-generated from Service Repeat",  # Hardcoded
                "service_repeat": repeat.name,  # Link back to Service Repeat
                "service_request_type": repeat.service_request_type,  # From Service Repeat
                "assigned_truckstore": repeat.assigned_truckstore,  # From Service Repeat
                "services": []  # This will hold the copied child table
            })

            # Fetch Service Items from Service Repeat and copy them
            service_items = frappe.get_all("Service Items Child Table",
                filters={"parent": repeat.name, "parenttype": "Service Repeat"},
                fields=["item_code", "item_name", "description", "quantity", "rate", 
                        "fetched_rate", "amount", "rate_changed", "tax_applicable", 
                        "pet", "pet_name", "pet_breed"]
            )

            for item in service_items:
                new_service_request.append("services", {
                    "item_code": item.item_code,
                    "item_name": item.item_name,
                    "description": item.description,
                    "quantity": item.quantity,
                    "rate": item.rate,
                    "fetched_rate": item.fetched_rate,
                    "amount": item.amount,
                    "rate_changed": item.rate_changed,
                    "tax_applicable": item.tax_applicable,
                    "pet": item.pet,
                    "pet_name": item.pet_name,
                    "pet_breed": item.pet_breed
                })

            new_service_request.insert(ignore_permissions=True)
            frappe.db.commit()

def get_upcoming_service_dates(start_date, recurrence_frequency, today, generation_window):
    """
    Calculate all upcoming service dates within the generation window.
    """
    upcoming_dates = []
    service_date = start_date
    while service_date <= add_days(today, generation_window):

        if service_date > today:  # Only consider future dates
            upcoming_dates.append(service_date)

        if recurrence_frequency == "Monthly":
            service_date = add_months(service_date, 1)
        elif recurrence_frequency == "Biweekly":
            service_date = add_days(service_date, 14)
        elif recurrence_frequency == "Weekly":
            service_date = add_days(service_date, 7)
        else:
            break  # Unknown recurrence type

    return upcoming_dates
