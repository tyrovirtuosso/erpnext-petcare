import frappe
from frappe import _
from datetime import datetime
from typing import Dict, List, Optional

def create_call_outcome(
    call_task: str,
    outcome_type: str,
    notes: str,
    next_action: str = None,
    follow_up_date: str = None,
    voxbay_call_log: str = None,
    customer_feedback: str = None,
    satisfaction_rating: str = None,
    call_duration: str = None
) -> str:
    """
    Create a new call outcome.
    
    Args:
        call_task: Name of the related call task
        outcome_type: Type of outcome (No Answer, Not Interested, Call Next Month, etc.)
        notes: Notes from the conversation
        next_action: Next action to take (Schedule Follow-up, Escalate to Supervisor, etc.)
        follow_up_date: Date for follow-up (if applicable)
        voxbay_call_log: Related Voxbay call log (if applicable)
        customer_feedback: Feedback from the customer
        satisfaction_rating: Customer satisfaction rating
        call_duration: Duration of the call
        
    Returns:
        str: Name of the created call outcome
    """
    try:
        # Validate inputs
        if not frappe.db.exists("Call Task", call_task):
            frappe.throw(_("Call Task {0} does not exist").format(call_task))
            
        if voxbay_call_log and not frappe.db.exists("Voxbay Call Log", voxbay_call_log):
            frappe.throw(_("Voxbay Call Log {0} does not exist").format(voxbay_call_log))
        
        # Create the call outcome
        outcome = frappe.new_doc("Call Outcome")
        outcome.call_task = call_task
        outcome.outcome_type = outcome_type
        outcome.notes = notes
        outcome.next_action = next_action
        outcome.follow_up_date = follow_up_date
        outcome.voxbay_call_log = voxbay_call_log
        outcome.customer_feedback = customer_feedback
        outcome.satisfaction_rating = satisfaction_rating
        outcome.call_duration = call_duration
        outcome.call_date = frappe.utils.now_datetime()
        
        outcome.insert(ignore_permissions=True)
        frappe.db.commit()
        
        # Update the call task status
        from .call_task import update_call_task_status
        update_call_task_status(
            call_task=call_task,
            status="Completed",
            call_outcome=outcome.name,
            call_duration=call_duration
        )
        
        return outcome.name
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error creating call outcome")
        frappe.throw(_("Failed to create call outcome: {0}").format(str(e)))

def get_customer_call_history(
    customer: str,
    limit: int = 10
) -> List[Dict]:
    """
    Get call history for a customer.
    
    Args:
        customer: Customer ID
        limit: Maximum number of records to return
        
    Returns:
        List of call outcomes with related task information
    """
    try:
        if not frappe.db.exists("Customer", customer):
            frappe.throw(_("Customer {0} does not exist").format(customer))
            
        # Get call tasks for the customer
        tasks = frappe.get_all(
            "Call Task",
            filters={"customer": customer},
            fields=["name"]
        )
        
        task_names = [task.name for task in tasks]
        
        if not task_names:
            return []
            
        # Get call outcomes for these tasks
        outcomes = frappe.get_all(
            "Call Outcome",
            filters={"call_task": ["in", task_names]},
            fields=["name", "outcome_type", "call_date", "notes", "satisfaction_rating"],
            order_by="call_date desc",
            limit=limit
        )
        
        # Add task details to each outcome
        for outcome in outcomes:
            task = frappe.get_doc("Call Task", outcome.call_task)
            outcome.task_type = task.task_type
            outcome.assigned_agent = task.assigned_agent
            
            # Get agent name
            if task.assigned_agent:
                agent = frappe.get_doc("User", task.assigned_agent)
                outcome.agent_name = agent.full_name
        
        return outcomes
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error getting customer call history")
        frappe.throw(_("Failed to get customer call history: {0}").format(str(e)))

@frappe.whitelist()
def create_follow_up_from_outcome(
    call_outcome: str,
    follow_up_date: str,
    follow_up_time: str = "09:00:00"
) -> str:
    """
    Create a follow-up task from a call outcome.
    
    Args:
        call_outcome: Name of the call outcome
        follow_up_date: Follow-up date in YYYY-MM-DD format
        follow_up_time: Follow-up time in HH:MM:SS format
        
    Returns:
        str: Name of the created follow-up task
    """
    try:
        from .call_task import create_follow_up_task
        return create_follow_up_task(
            call_outcome=call_outcome,
            follow_up_date=follow_up_date,
            follow_up_time=follow_up_time
        )
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error creating follow-up from outcome")
        frappe.throw(_("Failed to create follow-up: {0}").format(str(e))) 