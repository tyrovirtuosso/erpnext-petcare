import frappe
from frappe import _
from datetime import datetime, timedelta
from typing import Dict, List, Optional

def calculate_agent_metrics(
    agent: str,
    from_date: str,
    to_date: str
) -> Dict:
    """
    Calculate metrics for an agent over a date range.
    
    Args:
        agent: User ID of the agent
        from_date: Start date in YYYY-MM-DD format
        to_date: End date in YYYY-MM-DD format
        
    Returns:
        Dict: Agent metrics
    """
    try:
        if not frappe.db.exists("User", agent):
            frappe.throw(_("User {0} does not exist").format(agent))
            
        # Get all call tasks for the agent in the date range
        tasks = frappe.get_all(
            "Call Task",
            filters={
                "assigned_agent": agent,
                "due_date": ["between", [from_date, to_date]]
            },
            fields=["name", "status", "task_type", "priority"]
        )
        
        task_names = [task.name for task in tasks]
        
        # Get all call outcomes for these tasks
        outcomes = frappe.get_all(
            "Call Outcome",
            filters={"call_task": ["in", task_names]},
            fields=["name", "outcome_type", "call_duration"]
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
            
        # Calculate average call duration
        total_duration = 0
        duration_count = 0
        for outcome in outcomes:
            if outcome.call_duration:
                # Assuming call_duration is in seconds
                total_duration += int(outcome.call_duration)
                duration_count += 1
                
        avg_duration = total_duration / duration_count if duration_count > 0 else 0
        
        # Calculate follow-up rate
        follow_up_count = 0
        for outcome in outcomes:
            if outcome.outcome_type in ["No Answer", "Call Next Month"]:
                follow_up_count += 1
                
        follow_up_rate = (follow_up_count / total_outcomes * 100) if total_outcomes > 0 else 0
        
        # Calculate conversion rate (interested / total)
        interested_count = outcome_counts.get("Interested", 0)
        conversion_rate = (interested_count / total_outcomes * 100) if total_outcomes > 0 else 0
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "completion_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            "total_outcomes": total_outcomes,
            "outcome_counts": outcome_counts,
            "avg_call_duration": avg_duration,
            "follow_up_rate": follow_up_rate,
            "conversion_rate": conversion_rate
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error calculating agent metrics")
        frappe.throw(_("Failed to calculate agent metrics: {0}").format(str(e)))

def save_agent_metrics(
    agent: str,
    from_date: str,
    to_date: str
) -> str:
    """
    Calculate and save metrics for an agent.
    
    Args:
        agent: User ID of the agent
        from_date: Start date in YYYY-MM-DD format
        to_date: End date in YYYY-MM-DD format
        
    Returns:
        str: Name of the created metrics document
    """
    try:
        # Calculate metrics
        metrics = calculate_agent_metrics(agent, from_date, to_date)
        
        # Create metrics document
        doc = frappe.new_doc("Call Metrics")
        doc.agent = agent
        doc.from_date = from_date
        doc.to_date = to_date
        doc.calls_completed = metrics["completed_tasks"]
        doc.calls_missed = metrics["total_tasks"] - metrics["completed_tasks"]
        
        # Set outcome counts
        doc.no_answer_count = metrics["outcome_counts"].get("No Answer", 0)
        doc.not_interested_count = metrics["outcome_counts"].get("Not Interested", 0)
        doc.interested_count = metrics["outcome_counts"].get("Interested", 0)
        
        # Set other metrics
        doc.avg_call_duration = metrics["avg_call_duration"]
        doc.follow_up_rate = metrics["follow_up_rate"]
        doc.conversion_rate = metrics["conversion_rate"]
        
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        
        return doc.name
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error saving agent metrics")
        frappe.throw(_("Failed to save agent metrics: {0}").format(str(e)))

def get_team_metrics(
    from_date: str,
    to_date: str
) -> Dict:
    """
    Calculate metrics for the entire team.
    
    Args:
        from_date: Start date in YYYY-MM-DD format
        to_date: End date in YYYY-MM-DD format
        
    Returns:
        Dict: Team metrics
    """
    try:
        # Get all agents
        agents = frappe.get_all(
            "User",
            filters={"enabled": 1},
            fields=["name", "full_name"]
        )
        
        # Calculate metrics for each agent
        agent_metrics = {}
        for agent in agents:
            metrics = calculate_agent_metrics(agent.name, from_date, to_date)
            agent_metrics[agent.name] = {
                "name": agent.full_name,
                "metrics": metrics
            }
            
        # Calculate team totals
        total_tasks = sum(metrics["metrics"]["total_tasks"] for metrics in agent_metrics.values())
        total_completed = sum(metrics["metrics"]["completed_tasks"] for metrics in agent_metrics.values())
        total_outcomes = sum(metrics["metrics"]["total_outcomes"] for metrics in agent_metrics.values())
        
        # Calculate team averages
        avg_completion_rate = sum(metrics["metrics"]["completion_rate"] for metrics in agent_metrics.values()) / len(agent_metrics) if agent_metrics else 0
        avg_follow_up_rate = sum(metrics["metrics"]["follow_up_rate"] for metrics in agent_metrics.values()) / len(agent_metrics) if agent_metrics else 0
        avg_conversion_rate = sum(metrics["metrics"]["conversion_rate"] for metrics in agent_metrics.values()) / len(agent_metrics) if agent_metrics else 0
        
        return {
            "total_tasks": total_tasks,
            "total_completed": total_completed,
            "completion_rate": (total_completed / total_tasks * 100) if total_tasks > 0 else 0,
            "total_outcomes": total_outcomes,
            "avg_completion_rate": avg_completion_rate,
            "avg_follow_up_rate": avg_follow_up_rate,
            "avg_conversion_rate": avg_conversion_rate,
            "agent_metrics": agent_metrics
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error calculating team metrics")
        frappe.throw(_("Failed to calculate team metrics: {0}").format(str(e)))

@frappe.whitelist()
def get_agent_performance_report(
    from_date: str = None,
    to_date: str = None,
    agent: str = None
) -> Dict:
    """
    Generate a performance report for agents.
    
    Args:
        from_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
        to_date: End date in YYYY-MM-DD format (defaults to today)
        agent: Optional user ID to filter by agent
        
    Returns:
        Dict: Performance report data
    """
    try:
        # Set default date range if not provided
        if not from_date:
            from_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            
        if not to_date:
            to_date = datetime.now().strftime("%Y-%m-%d")
            
        # Get team metrics
        team_metrics = get_team_metrics(from_date, to_date)
        
        # Filter by agent if specified
        if agent:
            if agent not in team_metrics["agent_metrics"]:
                frappe.throw(_("Agent {0} not found in metrics").format(agent))
                
            agent_metrics = {agent: team_metrics["agent_metrics"][agent]}
        else:
            agent_metrics = team_metrics["agent_metrics"]
            
        return {
            "from_date": from_date,
            "to_date": to_date,
            "team_metrics": {
                "total_tasks": team_metrics["total_tasks"],
                "total_completed": team_metrics["total_completed"],
                "completion_rate": team_metrics["completion_rate"],
                "avg_completion_rate": team_metrics["avg_completion_rate"],
                "avg_follow_up_rate": team_metrics["avg_follow_up_rate"],
                "avg_conversion_rate": team_metrics["avg_conversion_rate"]
            },
            "agent_metrics": agent_metrics
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Error generating performance report")
        frappe.throw(_("Failed to generate performance report: {0}").format(str(e))) 