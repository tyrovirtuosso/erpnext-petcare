"""
This module manages the automated customer tagging system in PetCare.
It handles tag assignment, tag descriptions, and action guides based on customer behavior.
"""

import frappe
from datetime import date, timedelta
import numpy as np
from typing import Dict, List, Optional

class CustomerTagManager:
    """
    Manages customer tags based on service history, spending patterns, and pet ownership.
    Provides functionality for:
    - Determining appropriate tags
    - Updating customer tags
    - Generating action guides
    - Managing tag descriptions
    """

    def __init__(self):
        """Initialize dates for calculations."""
        self.today = date.today()
        self.six_months_ago = self.today - timedelta(days=180)
        self.one_month_ago = self.today - timedelta(days=30)
        self.one_year_ago = self.today - timedelta(days=365)
        self.three_months_ago = self.today - timedelta(days=90)

    def get_customer_service_data(self, customer: str) -> Dict:
        """Get all relevant service data for a customer."""
        try:
            service_requests = frappe.get_all(
                "Service Request",
                filters={
                    "customer": customer,
                    "status": "Completed",
                    "amount_after_discount": [">", 0]
                },
                fields=["completed_date", "amount_after_discount", "name"]
            )

            if not service_requests:
                return {
                    "service_count": 0,
                    "total_spent": 0,
                    "latest_service": None,
                    "services": [],
                    "recent_services": [],
                    "long_term_services": []
                }

            recent_services = [
                sr for sr in service_requests 
                if sr.completed_date >= self.three_months_ago
            ]
            long_term_services = [
                sr for sr in service_requests 
                if sr.completed_date >= self.one_year_ago
            ]

            return {
                "service_count": len(service_requests),
                "total_spent": sum(sr.amount_after_discount for sr in service_requests),
                "latest_service": max(sr.completed_date for sr in service_requests),
                "services": service_requests,
                "recent_services": recent_services,
                "long_term_services": long_term_services
            }
        except Exception as e:
            frappe.log_error(f"Error getting service data for customer {customer}: {str(e)}")
            return None

    def calculate_spending_percentiles(self) -> Dict:
        """Calculate spending percentiles across all customers."""
        try:
            all_customer_spending = frappe.db.sql("""
                SELECT customer, SUM(amount_after_discount) as total_spent
                FROM `tabService Request`
                WHERE status = 'Completed' AND amount_after_discount > 0
                GROUP BY customer
            """, as_dict=True)

            if not all_customer_spending:
                return {"median": 0, "percentile_90": 0}

            spend_values = [cs.total_spent for cs in all_customer_spending]
            return {
                "median": np.percentile(spend_values, 50),
                "percentile_90": np.percentile(spend_values, 90)
            }
        except Exception as e:
            frappe.log_error(f"Error calculating spending percentiles: {str(e)}")
            return {"median": 0, "percentile_90": 0}

    def determine_customer_tags(self, customer: str, service_data: Dict, spending_percentiles: Dict) -> List[str]:
        """
        Determine which tags should be applied to a customer based on their data.
        
        Args:
            customer (str): Customer ID
            service_data (Dict): Dictionary containing customer's service history and spending
            spending_percentiles (Dict): Dictionary with spending percentile thresholds
            
        Returns:
            List[str]: List of tags to be applied to the customer
        """
        if not service_data:
            return []

        tags = []

        # First-Time Customer
        if service_data["service_count"] == 1:
            tags.append("First-Time Customer")

        # Repeat Customer
        if service_data["service_count"] > 1:
            tags.append("Repeat Customer")

        # High-Value Customer
        if service_data["total_spent"] > spending_percentiles["median"]:
            tags.append("High-Value Customer")

        # VIP Customer
        if service_data["total_spent"] > spending_percentiles["percentile_90"]:
            tags.append("VIP Customer")

        # Inactive Customer
        if service_data["latest_service"] and service_data["latest_service"] < self.six_months_ago:
            tags.append("Inactive Customer")

        # Recently Active
        if service_data["latest_service"] and service_data["latest_service"] >= self.one_month_ago:
            tags.append("Recently Active")

        # Frequent Customer
        if len(service_data["recent_services"]) >= 3:
            tags.append("Frequent Customer")

        # Loyal Customer
        if len(service_data["long_term_services"]) >= 4:
            tags.append("Loyal Customer")

        # Multiple Pets Owner
        pet_count = frappe.db.count("Pet", {"owner": customer})
        if pet_count > 1:
            tags.append("Multiple Pets Owner")

        return tags

    def update_customer_tags(self, customer: str, tags: List[str]) -> None:
        """
        Update tags for a specific customer and generate associated guides.
        
        Args:
            customer (str): Customer ID to update
            tags (List[str]): List of tags to apply
        """
        try:
            # Get the customer document
            customer_doc = frappe.get_doc("Customer", customer)

            # Clear existing tags
            customer_doc.set("custom_customer_tags", [])
            
            # Add new tags
            for tag in tags:
                customer_doc.append("custom_customer_tags", {
                    "tag": tag,
                    "assigned_date": self.today,
                    "assigned_by": "Administrator",
                    "is_automatic": 1
                })
            
            # Update the tag actions guide and descriptions
            customer_doc.custom_tag_actions_guide = self.get_tag_actions_guide(tags)
            customer_doc.custom_tag_descriptions = self.get_tag_descriptions(tags)
            
            # Save the document
            customer_doc.save(ignore_permissions=True)
            print(f"Successfully updated tags and guides for {customer}")
            
        except Exception as e:
            frappe.log_error(f"Error updating tags for customer {customer}: {str(e)}")
            print(f"Error updating tags for {customer}: {str(e)}")

    def process_all_customers(self) -> None:
        """
        Process and update tags for all customers in the system.
        Handles database transactions and error logging.
        """
        try:
            # Get spending percentiles first
            spending_percentiles = self.calculate_spending_percentiles()

            # Get all customers
            customers = frappe.get_all("Customer", pluck="name")
            
            for customer in customers:
                service_data = self.get_customer_service_data(customer)
                if service_data:
                    tags = self.determine_customer_tags(customer, service_data, spending_percentiles)
                    self.update_customer_tags(customer, tags)

            frappe.db.commit()
            print("✅ Customer tags updated successfully!")

        except Exception as e:
            frappe.db.rollback()
            frappe.log_error(f"Error in customer tag update process: {str(e)}")
            print("❌ Error updating customer tags. Check error log for details.")

    def get_tag_actions_guide(self, tags: List[str]) -> str:
        """
        Generate a formatted guide for actions based on customer tags.
        
        Args:
            tags (List[str]): List of customer's current tags
            
        Returns:
            str: Formatted HTML string containing recommended actions
        """
        tag_actions = {
            "Active Customer": {
                "status": "✅ Active",
                "actions": [
                    "Maintain regular communication",
                    "Ask for referrals",
                    "Introduce new services"
                ]
            },
            "Inactive Customer": {
                "status": "⚠️ Needs Attention",
                "actions": [
                    "Schedule follow-up call",
                    "Send special comeback offer",
                    "Review last service feedback"
                ]
            },
            "First-Time Customer": {
                "status": "🆕 New",
                "actions": [
                    "Follow up within 48 hours",
                    "Get service feedback",
                    "Share loyalty program benefits"
                ]
            },
            "Regular Customer": {
                "status": "👍 Regular",
                "actions": [
                    "Maintain service quality",
                    "Suggest additional services",
                    "Consider for loyalty program"
                ]
            },
            "Loyal Customer": {
                "status": "⭐ Loyal",
                "actions": [
                    "Provide priority booking",
                    "Offer exclusive services",
                    "Send appreciation message"
                ]
            },
            "High-Value Customer": {
                "status": "💎 High Value",
                "actions": [
                    "Provide premium service options",
                    "Assign dedicated staff member",
                    "Regular personal check-ins"
                ]
            },
            "VIP Customer": {
                "status": "👑 VIP",
                "actions": [
                    "Priority scheduling",
                    "Personalized service plans",
                    "Direct manager contact"
                ]
            },
            "Multiple Pets Owner": {
                "status": "🐾 Multiple Pets",
                "actions": [
                    "Offer multi-pet discounts",
                    "Suggest combined appointments",
                    "Share multi-pet care tips"
                ]
            }
        }

        guide = "RECOMMENDED ACTIONS:\n\n"
        
        active_tags = [tag for tag in tags if tag in tag_actions]
        
        if not active_tags:
            guide += "No active tags to show actions for."
        else:
            for tag in active_tags:
                actions = tag_actions[tag]
                guide += f"{actions['status']} - {tag}\n"
                for action in actions['actions']:
                    guide += f"• {action}\n"
                guide += "\n"

        return guide

    def get_tag_descriptions(self, tags: List[str]) -> str:
        """
        Generate descriptions for customer's current tags.
        
        Args:
            tags (List[str]): List of customer's current tags
            
        Returns:
            str: Formatted string containing tag descriptions
        """
        tag_descriptions = {
            "Active Customer": "Customer who has had a service within the last 30 days. Shows regular engagement with our services.",
            "Recently Active": "Customer who has had a service within the last 30 days. Shows current engagement with our services.",
            "Inactive Customer": "Customer who hasn't had any services in the last 180 days. May need re-engagement efforts.",
            "First-Time Customer": "Has completed exactly one service with us. Critical period for customer retention.",
            "Regular Customer": "Has completed more than one service. Shows repeated trust in our services.",
            "Repeat Customer": "Has completed more than one service. Shows customer satisfaction and trust.",
            "Loyal Customer": "Has been consistently using our services for over 6 months with regular visits.",
            "High-Value Customer": "Total spending is above the median customer spending. Values our premium services.",
            "VIP Customer": "Among our top 10% of customers by spending. Highest value customer segment.",
            "Multiple Pets Owner": "Has more than one pet registered with us. Higher potential for multiple services.",
            "Frequent Customer": "Has at least 3 services in the last 3 months. Shows strong current engagement."
        }

        descriptions = "CURRENT TAG DESCRIPTIONS:\n\n"
        
        customer_tags = [tag for tag in tags if tag in tag_descriptions]
        
        if not customer_tags:
            descriptions += "No tags to describe."
        else:
            for tag in customer_tags:
                descriptions += f"📌 {tag}\n"
                descriptions += f"   {tag_descriptions[tag]}\n\n"

        # Add warning for any tags that don't have descriptions
        missing_tags = [tag for tag in tags if tag not in tag_descriptions]
        if missing_tags:
            descriptions += "\n⚠️ Tags without descriptions:\n"
            for tag in missing_tags:
                descriptions += f"• {tag}\n"

        return descriptions

def update_customer_tags():
    """
    Entry point function to update customer tags.
    Creates a CustomerTagManager instance and processes all customers.
    """
    manager = CustomerTagManager()
    manager.process_all_customers()

@frappe.whitelist()
def run_update(customer=None):
    """
    API endpoint to run the tag update process.
    Can update either a single customer or all customers.
    
    Args:
        customer (str, optional): Customer ID to update. If None, updates all customers.
        
    Returns:
        str: Success message indicating what was updated
    """
    manager = CustomerTagManager()
    
    if customer:
        # Update single customer
        service_data = manager.get_customer_service_data(customer)
        spending_percentiles = manager.calculate_spending_percentiles()
        tags = manager.determine_customer_tags(customer, service_data, spending_percentiles)
        manager.update_customer_tags(customer, tags)
        frappe.db.commit()
        return "Customer tags updated successfully"
    else:
        # Update all customers
        manager.process_all_customers()
        return "All customers' tags updated successfully"

# Usage Instructions:
# To run the script from bench console:
# bench console
# from petcare.scripts.update_customer_tags import update_customer_tags
# update_customer_tags()
