import frappe
from frappe import _
from typing import Dict
from .call_task_utils import (
    get_customers_for_followup_ordered,
    check_existing_task,
    create_call_task,
    populate_call_history,
    populate_voxbay_calls
)

@frappe.whitelist()
def create_followup_tasks(limit: int = None) -> Dict:
    """
    Create follow-up tasks for customers who haven't had service in 30+ days.
    
    Args:
        limit: Optional limit on number of tasks to create
        
    Returns:
        Dict containing success status and created tasks
    """
    try:
        if not limit:
            limit = 10  # Default if not provided

        half = limit // 2

        # Get top half (descending) for Sivagauri
        descending_customers = get_customers_for_followup_ordered(half, order="desc")
        # Get bottom half (ascending) for Pavithra
        ascending_customers = get_customers_for_followup_ordered(half, order="asc")

        created_tasks = []
        skipped_customers = []

        # Assign to Sivagauri
        for customer in descending_customers:
            if check_existing_task(customer.name, "Customer Follow-up"):
                skipped_customers.append(customer.name)
                continue
            task_name = create_call_task(
                customer=customer.name,
                agent="sivagauri27@gmail.com",
                task_type="Customer Follow-up",
                status="Pending"
            )
            populate_call_history(task_name)
            populate_voxbay_calls(task_name)
            created_tasks.append({
                "task": task_name,
                "customer": customer.name,
                "agent": "sivagauri27@gmail.com",
                "days_since_last_service": customer.custom_days_since_last_service
            })

        # Assign to Pavithra
        for customer in ascending_customers:
            if check_existing_task(customer.name, "Customer Follow-up"):
                skipped_customers.append(customer.name)
                continue
            task_name = create_call_task(
                customer=customer.name,
                agent="pavithra@masterpetindia.com",
                task_type="Customer Follow-up",
                status="Pending"
            )
            populate_call_history(task_name)
            populate_voxbay_calls(task_name)
            created_tasks.append({
                "task": task_name,
                "customer": customer.name,
                "agent": "pavithra@masterpetindia.com",
                "days_since_last_service": customer.custom_days_since_last_service
            })

        return {
            "success": True,
            "created_tasks": created_tasks,
            "skipped_customers": skipped_customers,
            "total_created": len(created_tasks),
            "total_skipped": len(skipped_customers)
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error creating follow-up tasks")
        return {
            "success": False,
            "message": str(e)
        }

# In bench console
# frappe.call('petcare.api.call_task.create_followup_tasks.create_followup_tasks', limit=100)