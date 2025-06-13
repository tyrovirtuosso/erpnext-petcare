"""
This file contains scheduler events for PetCare.
"""

import frappe
from frappe.utils import now_datetime
from petcare.scripts.update_customer_service_details import update_customer_service_details
from petcare.scripts.update_customer_tags import CustomerTagManager

def daily_customer_service_update():
    """
    Daily scheduled task to update customer service details and tags.
    Runs at 11:20 PM IST (17:50 UTC) every day.
    """
    try:
        # Update service details
        update_customer_service_details()
        
        # Update tags
        tag_manager = CustomerTagManager()
        tag_manager.process_all_customers()
        
        # Log success
        frappe.logger().info("Daily customer service update completed successfully")
        
    except Exception as e:
        # Log error
        frappe.logger().error(f"Error in daily customer service update: {str(e)}")
        frappe.log_error(f"Daily customer service update failed: {str(e)}")

# Scheduler configuration
scheduler_events = {
    "cron": {
        "50 17 * * *": [  # Run at 11:20 PM IST (17:50 UTC) every day
            "petcare.petcare.scheduler_events.daily_customer_service_update"
        ]
    }
} 