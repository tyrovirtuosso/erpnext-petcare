import frappe
from datetime import datetime
from typing import List, Dict, Optional

def get_customers_for_followup(limit: int = None) -> List[Dict]:
    """
    Get customers who have custom_days_since_last_service >= 30, sorted by days in descending order.
    
    Args:
        limit: Optional limit on number of customers to return
        
    Returns:
        List of customer dictionaries with required fields
    """
    customers = frappe.get_all(
        "Customer",
        filters={
            "disabled": 0,
            "custom_days_since_last_service": [">=", 30]
        },
        fields=[
            "name",
            "customer_name",
            "custom_days_since_last_service"
        ],
        order_by="custom_days_since_last_service desc"
    )
    
    if limit:
        customers = customers[:limit]
        
    return customers

def get_customers_for_followup_ordered(limit: int = None, order: str = "desc") -> List[Dict]:
    """
    Get customers for followup in specified order.
    order: "desc" for descending, "asc" for ascending
    """
    order_by = "custom_days_since_last_service desc" if order == "desc" else "custom_days_since_last_service asc"
    customers = frappe.get_all(
        "Customer",
        filters={
            "disabled": 0,
            "custom_days_since_last_service": [">=", 30]
        },
        fields=[
            "name",
            "customer_name",
            "custom_days_since_last_service"
        ],
        order_by=order_by
    )
    if limit:
        customers = customers[:limit]
    return customers

def check_existing_task(customer: str, task_type: str) -> bool:
    """
    Check if a customer already has a pending task of the given type,
    or a completed task of the same type within the last 30 days.
    
    Args:
        customer: Customer ID
        task_type: Type of task to check for
        
    Returns:
        bool: True if task exists, False otherwise
    """
    # Check for pending task
    pending_task = frappe.get_all(
        "Call Task",
        filters={
            "customer": customer,
            "task_type": task_type,
            "status": "Pending"
        },
        limit=1
    )
    if pending_task:
        return True

    # Check for completed task within last 30 days
    completed_tasks = frappe.get_all(
        "Call Task",
        filters={
            "customer": customer,
            "task_type": task_type,
            "status": "Completed"
        },
        fields=["date"],
        order_by="date desc",
        limit=1
    )
    if completed_tasks:
        from datetime import datetime
        last_completed_date = frappe.utils.getdate(completed_tasks[0]["date"])
        days_diff = (datetime.now().date() - last_completed_date).days
        if days_diff < 30:
            return True

    return False

def get_available_agents() -> List[str]:
    """
    Get list of available agents for task assignment.
    
    Returns:
        List of agent email addresses
    """
    return ["sivagauri27@gmail.com", "pavithra@masterpetindia.com"]

def assign_agent_to_task(agents: List[str], task_index: int) -> str:
    """
    Assign an agent to a task in round-robin fashion.
    
    Args:
        agents: List of available agents
        task_index: Index of the current task
        
    Returns:
        str: Assigned agent's email
    """
    return agents[task_index % len(agents)]

def update_customer_data_collection(customer: str, date: str, notes: str):
    """
    Update the customer's custom_data_collection field with the new note for the given date.
    If a note for the same date exists, replace it.
    """
    if not notes:
        return

    customer_doc = frappe.get_doc("Customer", customer)
    existing = customer_doc.custom_data_collection or ""
    lines = [line.strip() for line in existing.splitlines() if line.strip()]

    # Remove any note for the same date
    lines = [line for line in lines if not line.startswith(f"{date} -")]

    # Add the new note
    lines.append(f"{date} - {notes}")

    # Save back
    customer_doc.custom_data_collection = "\n".join(lines)
    customer_doc.save(ignore_permissions=True)
    frappe.db.commit()

def create_call_task(
    customer: str,
    agent: str,
    task_type: str = "Customer Follow-up",
    status: str = "Pending",
    notes: str = ""
) -> str:
    """
    Create a new call task.
    
    Args:
        customer: Customer ID
        agent: Agent email
        task_type: Type of task
        status: Task status
        notes: Notes for the call task
        
    Returns:
        str: Name of created call task
    """
    try:
        call_task = frappe.new_doc("Call Task")
        call_task.customer = customer
        call_task.agent = agent
        call_task.task_type = task_type
        call_task.status = status
        call_task.date = frappe.utils.today()
        if notes:
            call_task.notes = notes

        call_task.insert(ignore_permissions=True)
        frappe.db.commit()

        # Update customer data collection if notes present
        if notes:
            update_customer_data_collection(customer, call_task.date, notes)

        return call_task.name
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error creating call task")
        frappe.throw(f"Failed to create call task: {str(e)}")

def populate_call_history(call_task: str) -> None:
    """
    Populate call history for a call task, excluding the current task itself.
    
    Args:
        call_task: Name of the call task
    """
    try:
        doc = frappe.get_doc("Call Task", call_task)
        
        # Get call history, EXCLUDING the current task
        call_history = frappe.get_all(
            "Call Task",
            filters={
                "customer": doc.customer,
                "date": ["<=", doc.date],
                "name": ["!=", doc.name],  # Exclude the current task
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
        
        # Clear existing history
        doc.call_history = []
        
        # Add new history
        for history in call_history:
            doc.append("call_history", history)
            
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error populating call history")
        frappe.throw(f"Failed to populate call history: {str(e)}")

def populate_voxbay_calls(call_task: str) -> None:
    """
    Populate Voxbay calls for a call task.
    
    Args:
        call_task: Name of the call task
    """
    try:
        doc = frappe.get_doc("Call Task", call_task)
        
        # Get Voxbay calls
        voxbay_calls = frappe.get_all(
            "Voxbay Call Log",
            filters={
                "customer": doc.customer
            },
            fields=[
                "name as voxbay_call_log",
                "status as call_status",
                "type as call_type",
                "from as from_number",
                "to as to_number",
                "start_time",
                "end_time",
                "customer",
                "customer_name",
                "agent_number",
                "recording_url"
            ]
        )
        
        # Clear existing calls
        doc.voxbay_call = []
        
        # Add new calls
        for call in voxbay_calls:
            doc.append("voxbay_call", call)
            
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error populating Voxbay calls")
        frappe.throw(f"Failed to populate Voxbay calls: {str(e)}") 