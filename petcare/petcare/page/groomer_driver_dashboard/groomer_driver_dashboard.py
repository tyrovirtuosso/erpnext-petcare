import frappe
from frappe.utils import today, add_days, getdate, flt

@frappe.whitelist()
def get_service_requests(status, selected_date=None):
    """
    Fetch service requests with status and date filtering
    """
    filters = {
        'status': status,
    }
    
    # Add date filter
    if selected_date:
        filters['scheduled_date'] = selected_date
    else:
        filters['scheduled_date'] = today()
    
    fields = [
        'name',
        'customer',
        'customer_name',
        'status',
        'service_request_type',
        'assigned_driver',
        'driver_phone',
        'scheduled_date',
        'total_pets',
        'territory',
        'total_amount'
    ]
    
    requests = frappe.get_list(
        'Service Request',
        filters=filters,
        fields=fields,
        order_by='scheduled_date desc'
    )
    
    # Get additional details
    for request in requests:
        # Get driver's full name if assigned
        if request.assigned_driver:
            contact = frappe.get_doc('Contact', request.assigned_driver)
            request.driver_name = contact.first_name + (' ' + contact.last_name if contact.last_name else '')
        else:
            request.driver_name = 'Unassigned'
            
        # Format scheduled time
        if request.scheduled_date:
            request.scheduled_time = frappe.utils.format_date(request.scheduled_date)
        else:
            request.scheduled_time = 'Not scheduled'
            
        # Format amount
        request.formatted_amount = frappe.utils.fmt_money(request.total_amount or 0, currency=frappe.defaults.get_global_default('currency'))
    
    return requests

@frappe.whitelist()
def update_service_request_status(request_id, status):
    """
    Update the status of a service request
    
    Args:
        request_id: ID of the service request
        status: New status to set
    """
    if not frappe.has_permission('Service Request', 'write'):
        frappe.throw('Not permitted to update Service Request')
        
    # Validate status
    valid_statuses = [
        'Pending Assignment',
        'Awaiting Scheduling',
        'Scheduled',
        'Completed',
        'Cancelled'
    ]
    
    if status not in valid_statuses:
        frappe.throw(f'Invalid status. Must be one of: {", ".join(valid_statuses)}')
    
    doc = frappe.get_doc('Service Request', request_id)
    doc.status = status
    
    # Set completed date if status is Completed
    if status == 'Completed' and not doc.completed_date:
        doc.completed_date = frappe.utils.now()
    
    doc.save()
    frappe.db.commit()
    
    return {'message': 'Status updated successfully'}

@frappe.whitelist()
def get_financial_metrics(selected_date=None):
    if not selected_date:
        selected_date = today()
        
    metrics = {
        'scheduled_total': 0,
        'completed_total': 0,
        'three_day_avg': 0,
        'seven_day_avg': 0
    }
    
    selected_date = getdate(selected_date)
    
    # Get scheduled total for selected date
    scheduled = frappe.get_all(
        "Service Request",
        filters={
            "status": "Scheduled",
            "scheduled_date": selected_date
        },
        fields=["total_amount"]
    )
    metrics['scheduled_total'] = sum(flt(sr.total_amount) for sr in scheduled)
    
    # Get completed total for selected date
    completed = frappe.get_all(
        "Service Request",
        filters={
            "status": "Completed",
            "scheduled_date": selected_date
        },
        fields=["total_amount"]
    )
    metrics['completed_total'] = sum(flt(sr.total_amount) for sr in completed)
    
    # Calculate 3-day average
    three_day_total = 0
    for i in range(3):
        date = add_days(selected_date, -i)
        daily_completed = frappe.get_all(
            "Service Request",
            filters={
                "status": "Completed",
                "scheduled_date": date
            },
            fields=["total_amount"]
        )
        three_day_total += sum(flt(sr.total_amount) for sr in daily_completed)
    metrics['three_day_avg'] = three_day_total / 3
    
    # Calculate 7-day average
    seven_day_total = 0
    for i in range(7):
        date = add_days(selected_date, -i)
        daily_completed = frappe.get_all(
            "Service Request",
            filters={
                "status": "Completed",
                "scheduled_date": date
            },
            fields=["total_amount"]
        )
        seven_day_total += sum(flt(sr.total_amount) for sr in daily_completed)
    metrics['seven_day_avg'] = seven_day_total / 7
    
    return metrics 