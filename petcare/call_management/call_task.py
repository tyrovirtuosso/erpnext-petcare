import frappe
from frappe import _
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

def create_call_task(
    task_type: str,
    customer: str,
    due_date: str,
    due_time: str,
    assigned_agent: str,
    priority: str = "Medium",
    notes: str = "",
    service_request: str = None
) -> str:
    """
    Create a new call task.
    
    Args:
        task_type: Type of call task (Follow-up, Initial Contact, Post-Service, etc.)
        customer: Customer ID
        due_date: Due date in YYYY-MM-DD format
        due_time: Due time in HH:MM:SS format
        assigned_agent: User ID of the assigned agent
        priority: Priority of the task (High, Medium, Low)
        notes: Additional notes for the task
        service_request: Related service request ID (if applicable)
        
    Returns:
        str: Name of the created call task
    """
    try:
        # Validate inputs
        if not frappe.db.exists("Customer", customer):
            frappe.throw(_("Customer {0} does not exist").format(customer))
            
        if not frappe.db.exists("User", assigned_agent):
            frappe.throw(_("User {0} does not exist").format(assigned_agent))
            
        if service_request and not frappe.db.exists("Service Request", service_request):
            frappe.throw(_("Service Request {0} does not exist").format(service_request))
        
        # Create the call task
        call_task = frappe.new_doc("Call Task")
        call_task.task_type = task_type
        call_task.customer = customer
        call_task.due_date = due_date
        call_task.due_time = due_time
        call_task.assigned_agent = assigned_agent
        call_task.priority = priority
        call_task.notes = notes
        call_task.service_request = service_request
        call_task.status = "Pending"
        
        call_task.insert(ignore_permissions=True)
        frappe.db.commit()
        
        return call_task.name
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error creating call task")
        frappe.throw(_("Failed to create call task: {0}").format(str(e)))

def update_call_task_status(
    call_task: str,
    status: str,
    call_outcome: str = None,
    call_duration: str = None,
    notes: str = None
) -> None:
    """
    Update the status and related information of a call task.
    
    Args:
        call_task: Name of the call task
        status: New status (Pending, Scheduled, Completed, Cancelled)
        call_outcome: Related call outcome document (if applicable)
        call_duration: Duration of the call (if applicable)
        notes: Additional notes
    """
    try:
        if not frappe.db.exists("Call Task", call_task):
            frappe.throw(_("Call Task {0} does not exist").format(call_task))
            
        doc = frappe.get_doc("Call Task", call_task)
        doc.status = status
        
        if call_outcome:
            doc.call_outcome = call_outcome
            
        if call_duration:
            doc.call_duration = call_duration
            
        if notes:
            doc.notes = notes
            
        doc.last_call_date = frappe.utils.now_datetime()
        
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error updating call task status")
        frappe.throw(_("Failed to update call task status: {0}").format(str(e)))

def get_agent_tasks(
    agent: str,
    date: str = None,
    status: str = None,
    limit: int = 20
) -> List[Dict]:
    """
    Get call tasks assigned to an agent.
    
    Args:
        agent: User ID of the agent
        date: Filter by date (YYYY-MM-DD format)
        status: Filter by status
        limit: Maximum number of tasks to return
        
    Returns:
        List of call task documents
    """
    try:
        filters = {"assigned_agent": agent}
        
        if date:
            filters["due_date"] = date
            
        if status:
            filters["status"] = status
            
        tasks = frappe.get_all(
            "Call Task",
            filters=filters,
            fields=["name", "task_type", "customer", "due_date", "due_time", 
                   "priority", "status", "notes", "service_request"],
            order_by="due_date, due_time",
            limit=limit
        )
        
        return tasks
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error getting agent tasks")
        frappe.throw(_("Failed to get agent tasks: {0}").format(str(e)))

def create_follow_up_task(
    call_outcome: str,
    follow_up_date: str,
    follow_up_time: str = "09:00:00",
    assigned_agent: str = None
) -> str:
    """
    Create a follow-up task based on a call outcome.
    
    Args:
        call_outcome: Name of the call outcome document
        follow_up_date: Follow-up date in YYYY-MM-DD format
        follow_up_time: Follow-up time in HH:MM:SS format
        assigned_agent: User ID of the assigned agent (defaults to original agent)
        
    Returns:
        str: Name of the created follow-up task
    """
    try:
        if not frappe.db.exists("Call Outcome", call_outcome):
            frappe.throw(_("Call Outcome {0} does not exist").format(call_outcome))
            
        outcome = frappe.get_doc("Call Outcome", call_outcome)
        call_task = frappe.get_doc("Call Task", outcome.call_task)
        
        # If no agent specified, use the original agent
        if not assigned_agent:
            assigned_agent = call_task.assigned_agent
            
        # Create the follow-up task
        new_task = create_call_task(
            task_type="Follow-up",
            customer=call_task.customer,
            due_date=follow_up_date,
            due_time=follow_up_time,
            assigned_agent=assigned_agent,
            priority="Medium",
            notes=f"Follow-up for call on {outcome.call_date.strftime('%d-%m-%Y')}. Previous outcome: {outcome.outcome_type}",
            service_request=call_task.service_request
        )
        
        return new_task
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error creating follow-up task")
        frappe.throw(_("Failed to create follow-up task: {0}").format(str(e)))

@frappe.whitelist()
def get_today_tasks(agent: str = None) -> List[Dict]:
    """
    Get all call tasks scheduled for today.
    
    Args:
        agent: Optional user ID to filter by agent
        
    Returns:
        List of call task documents
    """
    try:
        today = frappe.utils.today()
        filters = {"due_date": today, "status": ["in", ["Pending", "Scheduled"]]}
        
        if agent:
            filters["assigned_agent"] = agent
            
        tasks = frappe.get_all(
            "Call Task",
            filters=filters,
            fields=["name", "task_type", "customer", "due_date", "due_time", 
                   "priority", "status", "notes", "service_request", "assigned_agent"],
            order_by="due_time"
        )
        
        # Add customer details
        for task in tasks:
            if task.customer:
                customer = frappe.get_doc("Customer", task.customer)
                task.customer_name = customer.customer_name
                task.mobile_no = customer.mobile_no
                
        return tasks
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error getting today's tasks")
        frappe.throw(_("Failed to get today's tasks: {0}").format(str(e))) 