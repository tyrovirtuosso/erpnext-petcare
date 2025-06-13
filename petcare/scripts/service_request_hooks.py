import frappe
from datetime import date

def update_latest_completed_service(doc, method):
    """Updates the latest completed service date and days since last service in the Customer doctype whenever a Service Request is completed."""
    
    if doc.status == "Completed" and doc.completed_date:
        latest_date = frappe.db.sql("""
            SELECT MAX(completed_date) 
            FROM `tabService Request`
            WHERE customer = %s AND status = 'Completed'
        """, (doc.customer,))[0][0]

        days_since_last_service = 0  # Default to 0 to prevent IntegrityError

        if latest_date:
            today = date.today()
            latest_service_date = latest_date if isinstance(latest_date, date) else latest_date.date()
            days_since_last_service = (today - latest_service_date).days

            frappe.db.set_value("Customer", doc.customer, "custom_latest_completed_service_date", latest_service_date)
        
        # Always update days since last service
        frappe.db.set_value("Customer", doc.customer, "custom_days_since_last_service", days_since_last_service)
        
        # Check if the customer has any service request
        service_request_exists = frappe.db.exists("Service Request", {"customer": doc.customer})

        if service_request_exists:
            frappe.db.set_value("Customer", doc.customer, "custom_lead_status", "Converted")

        frappe.db.commit()
