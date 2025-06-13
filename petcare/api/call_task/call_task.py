import frappe
from datetime import datetime, timedelta
from .call_task_utils import create_call_task, populate_call_history, populate_voxbay_calls, update_customer_data_collection

@frappe.whitelist()
def get_customer_call_history(customer, date, exclude_task):
    # Always exclude the current task from the call history
    call_tasks = frappe.get_all(
        "Call Task",
        filters={
            "customer": customer,
            "date": ["<=", date],
            "name": ["!=", exclude_task]
        },
        fields=[
            "name as call_task",
            "date",
            "task_type",
            "agent",
            "next_follow_up_date",
            "customer",
            "status"
        ]
    )
    return call_tasks 

@frappe.whitelist()
def get_active_customers_with_completed_services():
    """
    Returns all active customers (not disabled) who have at least one completed service request
    and their last completed service was more than 30 days ago
    """
    # Get all active customers with completed service requests
    customers = frappe.get_all(
        "Customer",
        filters={
            "disabled": 0  # 0 means not disabled
        },
        fields=[
            "name",
            "customer_name",
            "customer_group",
            "territory"
        ]
    )
    
    # Calculate the date 30 days ago
    thirty_days_ago = datetime.now() - timedelta(days=30)
    
    result = []
    for customer in customers:
        # Get the latest completed service request for each customer
        service_requests = frappe.get_all(
            "Service Request",
            filters={
                "customer": customer.name,
                "status": "Completed"
            },
            fields=[
                "name",
                "completed_date"
            ],
            order_by="completed_date desc",
            limit=1
        )
        
        if service_requests:
            completed_date = frappe.utils.getdate(service_requests[0].completed_date)
            # Only include customers whose last completed service was more than 30 days ago
            if completed_date < thirty_days_ago.date():
                customer["last_completed_date"] = service_requests[0].completed_date
                customer["last_completed_service"] = service_requests[0].name
                customer["days_since_last_service"] = (datetime.now().date() - completed_date).days
                result.append(customer)
    
    return result 

@frappe.whitelist()
def create_followup_from_next_date(call_task_name):
    doc = frappe.get_doc("Call Task", call_task_name)
    next_date = doc.next_follow_up_date
    if not next_date:
        frappe.throw("Next Follow Up Date is not set.")
    if doc.status != "Completed":
        return {"created": False, "reason": "Task is not completed. No follow-up will be created."}
    # Prevent duplicate (same customer, task_type, and date)
    existing = frappe.get_all(
        "Call Task",
        filters={
            "customer": doc.customer,
            "task_type": doc.task_type or "Customer Follow-up",
            "date": next_date,
        },
        limit=1
    )
    if existing:
        return {"created": False, "reason": "A follow-up task for this customer, type, and date already exists."}
    # Create
    new_task_name = create_call_task(
        customer=doc.customer,
        agent=doc.agent,
        task_type=doc.task_type or "Customer Follow-up",
        status="Pending"
    )
    new_task = frappe.get_doc("Call Task", new_task_name)
    new_task.date = next_date
    new_task.save(ignore_permissions=True)
    frappe.db.commit()
    populate_call_history(new_task_name)
    populate_voxbay_calls(new_task_name)
    return {"created": True, "task": new_task_name} 

def on_update(doc, method=None):
    """
    Sync notes to customer data collection on every update/save.
    """
    if doc.notes:
        update_customer_data_collection(doc.customer, doc.date, doc.notes) 