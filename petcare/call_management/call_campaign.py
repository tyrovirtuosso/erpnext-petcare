import frappe
from frappe import _
from datetime import datetime, timedelta
from typing import Dict, List, Optional

def create_call_campaign(
    campaign_name: str,
    start_date: str,
    end_date: str,
    campaign_goal: str,
    target_audience: str = None,
    success_metrics: str = None,
    notes: str = None
) -> str:
    """
    Create a new call campaign.
    
    Args:
        campaign_name: Name of the campaign
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        campaign_goal: Goal of the campaign
        target_audience: Target audience for the campaign
        success_metrics: Metrics to measure success
        notes: Additional notes
        
    Returns:
        str: Name of the created call campaign
    """
    try:
        # Create the call campaign
        campaign = frappe.new_doc("Call Campaign")
        campaign.campaign_name = campaign_name
        campaign.start_date = start_date
        campaign.end_date = end_date
        campaign.campaign_goal = campaign_goal
        campaign.target_audience = target_audience
        campaign.success_metrics = success_metrics
        campaign.notes = notes
        campaign.status = "Planning"
        
        campaign.insert(ignore_permissions=True)
        frappe.db.commit()
        
        return campaign.name
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error creating call campaign")
        frappe.throw(_("Failed to create call campaign: {0}").format(str(e)))

def add_agent_to_campaign(
    campaign: str,
    agent: str,
    target_calls: int = 0
) -> None:
    """
    Add an agent to a call campaign.
    
    Args:
        campaign: Name of the call campaign
        agent: User ID of the agent
        target_calls: Target number of calls for the agent
    """
    try:
        if not frappe.db.exists("Call Campaign", campaign):
            frappe.throw(_("Call Campaign {0} does not exist").format(campaign))
            
        if not frappe.db.exists("User", agent):
            frappe.throw(_("User {0} does not exist").format(agent))
            
        doc = frappe.get_doc("Call Campaign", campaign)
        
        # Check if agent is already assigned
        for assigned_agent in doc.assigned_agents:
            if assigned_agent.agent == agent:
                frappe.throw(_("Agent {0} is already assigned to this campaign").format(agent))
                
        # Add the agent
        doc.append("assigned_agents", {
            "agent": agent,
            "target_calls": target_calls,
            "completed_calls": 0
        })
        
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error adding agent to campaign")
        frappe.throw(_("Failed to add agent to campaign: {0}").format(str(e)))

def generate_campaign_tasks(
    campaign: str,
    task_type: str = "Sales Call",
    priority: str = "Medium",
    due_date: str = None
) -> int:
    """
    Generate call tasks for a campaign.
    
    Args:
        campaign: Name of the call campaign
        task_type: Type of call task
        priority: Priority of the tasks
        due_date: Due date for the tasks (defaults to campaign start date)
        
    Returns:
        int: Number of tasks created
    """
    try:
        if not frappe.db.exists("Call Campaign", campaign):
            frappe.throw(_("Call Campaign {0} does not exist").format(campaign))
            
        doc = frappe.get_doc("Call Campaign", campaign)
        
        if not doc.assigned_agents:
            frappe.throw(_("No agents assigned to this campaign"))
            
        # Determine target audience
        filters = {}
        if doc.target_audience == "New Customers":
            filters["creation"] = [">=", doc.start_date]
        elif doc.target_audience == "Repeat Customers":
            # This would need custom logic based on your definition of repeat customers
            pass
        elif doc.target_audience == "Leads":
            # Assuming leads are customers with a specific status
            filters["customer_status"] = ["in", ["New Lead", "Interested"]]
            
        # Get customers based on filters
        customers = frappe.get_all(
            "Customer",
            filters=filters,
            fields=["name"]
        )
        
        if not customers:
            frappe.throw(_("No customers found matching the target audience criteria"))
            
        # Set due date if not provided
        if not due_date:
            due_date = doc.start_date
            
        # Create tasks
        from .call_task import create_call_task
        tasks_created = 0
        
        # Distribute customers among agents
        agent_count = len(doc.assigned_agents)
        for i, customer in enumerate(customers):
            # Assign to agents in round-robin fashion
            agent_index = i % agent_count
            agent = doc.assigned_agents[agent_index].agent
            
            # Create the task
            create_call_task(
                task_type=task_type,
                customer=customer.name,
                due_date=due_date,
                due_time="09:00:00",  # Default time
                assigned_agent=agent,
                priority=priority,
                notes=f"Part of campaign: {campaign}"
            )
            
            tasks_created += 1
            
        # Update campaign status
        doc.status = "Active"
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        
        return tasks_created
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error generating campaign tasks")
        frappe.throw(_("Failed to generate campaign tasks: {0}").format(str(e)))

def get_campaign_metrics(
    campaign: str
) -> Dict:
    """
    Get metrics for a call campaign.
    
    Args:
        campaign: Name of the call campaign
        
    Returns:
        Dict: Campaign metrics
    """
    try:
        if not frappe.db.exists("Call Campaign", campaign):
            frappe.throw(_("Call Campaign {0} does not exist").format(campaign))
            
        doc = frappe.get_doc("Call Campaign", campaign)
        
        # Get all tasks for this campaign
        tasks = frappe.get_all(
            "Call Task",
            filters={"notes": ["like", f"%campaign: {campaign}%"]},
            fields=["name", "status", "assigned_agent"]
        )
        
        # Get all outcomes for these tasks
        task_names = [task.name for task in tasks]
        outcomes = frappe.get_all(
            "Call Outcome",
            filters={"call_task": ["in", task_names]},
            fields=["name", "outcome_type"]
        )
        
        # Calculate metrics
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.status == "Completed"])
        total_outcomes = len(outcomes)
        
        # Count outcomes by type
        outcome_counts = {}
        for outcome in outcomes:
            if outcome.outcome_type not in outcome_counts:
                outcome_counts[outcome.outcome_type] = 0
            outcome_counts[outcome.outcome_type] += 1
            
        # Calculate agent performance
        agent_performance = {}
        for task in tasks:
            if task.assigned_agent not in agent_performance:
                agent_performance[task.assigned_agent] = {
                    "total": 0,
                    "completed": 0
                }
            agent_performance[task.assigned_agent]["total"] += 1
            if task.status == "Completed":
                agent_performance[task.assigned_agent]["completed"] += 1
                
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "completion_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            "total_outcomes": total_outcomes,
            "outcome_counts": outcome_counts,
            "agent_performance": agent_performance
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error getting campaign metrics")
        frappe.throw(_("Failed to get campaign metrics: {0}").format(str(e)))

@frappe.whitelist()
def get_active_campaigns() -> List[Dict]:
    """
    Get all active call campaigns.
    
    Returns:
        List of active call campaigns
    """
    try:
        campaigns = frappe.get_all(
            "Call Campaign",
            filters={"status": "Active"},
            fields=["name", "campaign_name", "start_date", "end_date", "target_audience"]
        )
        
        return campaigns
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error getting active campaigns")
        frappe.throw(_("Failed to get active campaigns: {0}").format(str(e))) 