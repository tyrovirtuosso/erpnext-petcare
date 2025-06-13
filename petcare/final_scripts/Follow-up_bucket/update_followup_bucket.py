import frappe
from frappe.utils import now_datetime

def update_followup_bucket(customer_id=None):
    """
    Updates the custom_followup_bucket field for all customers based on their
    custom_days_since_last_service value.
    
    Args:
        customer_id (str, optional): Specific customer ID to update. If provided, only updates that customer.
    """
    # Get customer(s)
    if customer_id:
        customers = frappe.get_all("Customer", 
            filters={"name": customer_id},
            fields=["name", "custom_days_since_last_service"]
        )
    else:
        customers = frappe.get_all("Customer", 
            fields=["name", "custom_days_since_last_service"]
        )
    
    for customer in customers:
        days = customer.custom_days_since_last_service
        
        # Determine the bucket based on days
        if days is None or days == 0:
            bucket = "No Service History"
        elif days <= 30:
            bucket = "0-30 days"
        elif days <= 60:
            bucket = "31-60 days"
        elif days <= 90:
            bucket = "61-90 days"
        else:
            bucket = "91+ days"
        
        # Update the customer's followup bucket
        try:
            frappe.db.set_value(
                "Customer",
                customer.name,
                "custom_followup_bucket",
                bucket,
                update_modified=False
            )
            print(f"Updated customer {customer.name} to bucket: {bucket}")
        except Exception as e:
            frappe.log_error(
                f"Error updating followup bucket for customer {customer.name}: {str(e)}",
                "Followup Bucket Update Error"
            )
            print(f"Error updating customer {customer.name}: {str(e)}")

def execute():
    """
    Main execution function that will be called by the scheduler
    """
    # Test for specific customer
    # update_followup_bucket("CUST-2025-02036")
    
    update_followup_bucket()
    frappe.db.commit()

if __name__ == "__main__":
    execute() 