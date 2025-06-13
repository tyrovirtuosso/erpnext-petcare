"""
This module manages customer service details in the PetCare system.
It handles updating service dates, lead status, and integrates with the tagging system.
"""

import frappe
from datetime import date
from typing import Optional
from petcare.scripts.update_customer_tags import CustomerTagManager

class CustomerServiceManager:
    """
    Manages customer service-related operations including:
    - Tracking service dates
    - Updating lead status
    - Managing service history
    """

    def __init__(self):
        """Initialize with today's date for calculations."""
        self.today = date.today()

    def get_latest_service_date(self, customer: str) -> Optional[date]:
        """
        Get the latest completed service date for a customer.
        
        Args:
            customer (str): The customer ID to check
            
        Returns:
            Optional[date]: The date of the latest completed service, or None if no services
        """
        try:
            # Get all completed service requests for the customer
            latest_service = frappe.get_all(
                "Service Request",
                filters={
                    "customer": customer,
                    "status": "Completed"
                },
                fields=["completed_date"],
                order_by="completed_date DESC",
                limit=1
            )

            if latest_service:
                return latest_service[0].completed_date
            return None
            
        except Exception as e:
            frappe.log_error(f"Error getting latest service date for customer {customer}: {str(e)}")
            return None

    def calculate_days_since_service(self, latest_service_date: Optional[date]) -> int:
        """
        Calculate the number of days since the last service.
        
        Args:
            latest_service_date (Optional[date]): The date of the last service
            
        Returns:
            int: Number of days since last service, 0 if no service
        """
        if not latest_service_date:
            return 0
        return (self.today - latest_service_date).days

    def has_completed_service(self, customer: str) -> bool:
        """
        Check if a customer has any completed service requests.
        
        Args:
            customer (str): The customer ID to check
            
        Returns:
            bool: True if customer has completed services, False otherwise
        """
        return frappe.db.exists(
            "Service Request",
            {
                "customer": customer,
                "status": "Completed"
            }
        )

    def update_customer_details(self, customer: str) -> None:
        """
        Update service details for a specific customer.
        Updates:
        - Latest completed service date
        - Days since last service
        - Lead status (Converted/New Lead)
        
        Args:
            customer (str): The customer ID to update
        """
        try:
            # Get latest service date
            latest_service_date = self.get_latest_service_date(customer)
            
            # Calculate days since last service
            days_since_service = self.calculate_days_since_service(latest_service_date)
            
            # Get current lead status
            current_lead_status = frappe.db.get_value("Customer", customer, "custom_lead_status")
            
            # Check if customer has any completed service
            has_completed = self.has_completed_service(customer)
            
            # Determine lead status
            # If there's a completed service and status isn't already Converted, set to Converted
            # Otherwise, set to New Lead
            new_lead_status = "Converted" if has_completed else "New Lead"

            # Update customer document
            frappe.db.set_value(
                "Customer",
                customer,
                {
                    "custom_latest_completed_service_date": latest_service_date,
                    "custom_days_since_last_service": days_since_service,
                    "custom_lead_status": new_lead_status
                },
                update_modified=False
            )

            # Commit after each customer update
            frappe.db.commit()

            print(f"\nUpdated Customer {customer}:")
            print(f"Latest Service Date: {latest_service_date}")
            print(f"Days Since Service: {days_since_service}")
            print(f"Lead Status: {new_lead_status}")

        except Exception as e:
            frappe.db.rollback()
            frappe.log_error(f"Error updating service details for customer {customer}: {str(e)}")
            print(f"❌ Error updating customer {customer}: {str(e)}")

    def process_all_customers(self) -> None:
        """
        Process and update service details for all customers in the system.
        Handles database transactions and error logging.
        """
        customers = frappe.get_all("Customer", pluck="name")
        total_customers = len(customers)
        updated_count = 0
        error_count = 0
        
        print(f"\nProcessing {total_customers} customers...")
        
        for customer in customers:
            try:
                self.update_customer_details(customer)
                updated_count += 1
            except Exception as e:
                error_count += 1
                print(f"❌ Error processing customer {customer}: {str(e)}")
        
        print(f"\n✅ Update complete!")
        print(f"Successfully updated: {updated_count} customers")
        print(f"Errors encountered: {error_count} customers")

def update_customer_service_details():
    """
    Entry point function to update customer service details.
    Creates a CustomerServiceManager instance and processes all customers.
    """
    manager = CustomerServiceManager()
    manager.process_all_customers()

@frappe.whitelist()
def run_update(customer=None):
    """
    API endpoint to run the update process.
    Can update either a single customer or all customers.
    
    Args:
        customer (str, optional): Customer ID to update. If None, updates all customers.
        
    Returns:
        str: Success message indicating what was updated
    """
    manager = CustomerServiceManager()
    
    if customer:
        # Update single customer
        manager.update_customer_details(customer)
        # Update tags for this customer
        tag_manager = CustomerTagManager()
        service_data = tag_manager.get_customer_service_data(customer)
        spending_percentiles = tag_manager.calculate_spending_percentiles()
        tags = tag_manager.determine_customer_tags(customer, service_data, spending_percentiles)
        tag_manager.update_customer_tags(customer, tags)
        return "Customer updated successfully"
    else:
        # Update all customers
        manager.process_all_customers()
        # Update all tags
        tag_manager = CustomerTagManager()
        tag_manager.process_all_customers()
        return "All customers updated successfully"

# Usage Instructions:
# To run the script from bench console:
# bench console
# from petcare.scripts.update_customer_service_details import update_customer_service_details
# update_customer_service_details()

# Option 1: Using the update_customer_service_details function
# from petcare.scripts.update_customer_service_details import update_customer_service_details
# update_customer_service_details()

# # Option 2: Using the run_update function (same as clicking the "Update All Customers" button)
# from petcare.scripts.update_customer_service_details import run_update
# run_update()