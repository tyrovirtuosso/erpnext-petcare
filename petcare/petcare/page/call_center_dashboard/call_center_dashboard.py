import frappe
from datetime import datetime, timedelta

def check_permission():
    """Check if user has Petcare role"""
    if not frappe.has_permission("Voxbay Call Log", "read"):
        frappe.throw("Not permitted", frappe.PermissionError)
    
    if "Petcare" not in frappe.get_roles():
        frappe.throw("You need Petcare role to access this dashboard", frappe.PermissionError)

def get_agent_name(agent_number):
    """Get agent name based on their number"""
    if not agent_number:
        return None
    if agent_number == "919656420060":
        return "Sivagauri"
    elif agent_number == "919188896915":
        return "Pavithra"
    elif agent_number == "919037556420":
        return "Shane"
    return None  # Return None for unknown agent numbers

def get_contact_info(phone_number):
    """Get contact information for a phone number"""
    if not phone_number:
        return None
        
    # Clean the phone number
    cleaned_number = phone_number.replace("+", "").replace(" ", "")
    
    # Search for contact with the phone number
    contacts = frappe.get_all(
        "Contact",
        or_filters={
            "phone": ["like", f"%{cleaned_number}%"],
            "mobile_no": ["like", f"%{cleaned_number}%"]
        },
        fields=["name", "first_name", "last_name", "phone", "mobile_no"]
    )
    
    if not contacts:
        return None
        
    # Get the first matching contact
    contact = contacts[0]
    
    # Get all linked customers for this contact
    customer_links = frappe.get_all(
        "Dynamic Link",
        filters={
            "link_doctype": "Customer",
            "parenttype": "Contact",
            "parent": contact.name
        },
        fields=["link_name"]
    )
    
    # Get customer details including territory and customer name
    customers_info = []
    for link in customer_links:
        customer = frappe.get_doc("Customer", link.link_name)
        customers_info.append({
            "name": customer.name,
            "customer_name": customer.customer_name,
            "territory": customer.territory or "No Territory"
        })
    
    contact_info = {
        "phone": contact.phone,
        "mobile_no": contact.mobile_no,
        "customers": customers_info
    }
    
    return contact_info

@frappe.whitelist()
def get_agent_call_stats(start_date=None, end_date=None):
    """Get call statistics for each agent with date filtering, including 'No Agent' cases"""
    check_permission()
    
    # Include known agents and also cases where agent_number is NULL or empty
    agent_numbers = ["919656420060", "919188896915", "919037556420"]
    agent_numbers_str = ", ".join([f"'{num}'" for num in agent_numbers])
    conditions = f"(agent_number IN ({agent_numbers_str}) OR agent_number IS NULL OR agent_number = '')"
    if start_date and end_date:
        conditions += f" AND DATE(creation) BETWEEN '{start_date}' AND '{end_date}'"
    elif start_date:
        conditions += f" AND DATE(creation) >= '{start_date}'"
    elif end_date:
        conditions += f" AND DATE(creation) <= '{end_date}'"
    
    data = frappe.db.sql(f"""
        SELECT 
            COALESCE(NULLIF(agent_number, ''), 'NO_AGENT') as agent_number,
            COUNT(DISTINCT CASE 
                WHEN type = 'Incoming' AND status IN ('ANSWER', 'Completed') 
                THEN CONCAT(COALESCE(`from`, ''), '-', DATE(creation))
            END) as successful_incoming,
            COUNT(DISTINCT CASE 
                WHEN type = 'Incoming' AND status NOT IN ('ANSWER', 'Completed') 
                THEN CONCAT(COALESCE(`from`, ''), '-', DATE(creation))
            END) as failed_incoming,
            COUNT(DISTINCT CASE 
                WHEN type = 'Outgoing' AND status IN ('ANSWER', 'Completed') 
                THEN CONCAT(COALESCE(`to`, ''), '-', DATE(creation))
            END) as successful_outgoing,
            COUNT(DISTINCT CASE 
                WHEN type = 'Outgoing' AND status NOT IN ('ANSWER', 'Completed') 
                THEN CONCAT(COALESCE(`to`, ''), '-', DATE(creation))
            END) as failed_outgoing,
            COUNT(DISTINCT CASE 
                WHEN status IN ('ANSWER', 'Completed') 
                THEN CONCAT(
                    CASE 
                        WHEN type = 'Incoming' THEN COALESCE(`from`, '')
                        WHEN type = 'Outgoing' THEN COALESCE(`to`, '')
                    END,
                    '-',
                    DATE(creation)
                )
            END) as total_successful,
            COUNT(DISTINCT CASE 
                WHEN status NOT IN ('ANSWER', 'Completed') 
                THEN CONCAT(
                    CASE 
                        WHEN type = 'Incoming' THEN COALESCE(`from`, '')
                        WHEN type = 'Outgoing' THEN COALESCE(`to`, '')
                    END,
                    '-',
                    DATE(creation)
                )
            END) as total_failed
        FROM 
            `tabVoxbay Call Log`
        WHERE 
            {conditions}
        GROUP BY 
            COALESCE(NULLIF(agent_number, ''), 'NO_AGENT')
        ORDER BY 
            total_successful DESC
    """, as_dict=1)
    
    # Add agent names to the data, label 'No Agent' for missing agent_number
    for row in data:
        if row['agent_number'] == 'NO_AGENT':
            row['agent_name'] = 'No Agent'
        else:
            row['agent_name'] = get_agent_name(row['agent_number']) or row['agent_number']
    
    return data

@frappe.whitelist()
def get_detailed_calls(start_date=None, end_date=None, agent_number=None, status=None):
    """Get detailed call information with filters"""
    check_permission()
    
    conditions = []
    
    if start_date and end_date:
        conditions.append(f"DATE(creation) BETWEEN '{start_date}' AND '{end_date}'")
    elif start_date:
        conditions.append(f"DATE(creation) >= '{start_date}'")
    elif end_date:
        conditions.append(f"DATE(creation) <= '{end_date}'")
        
    if agent_number:
        if agent_number == "NO_AGENT":
            conditions.append("(agent_number IS NULL OR agent_number = '')")
        else:
            conditions.append(f"agent_number = '{agent_number}'")
    if status:
        if status == "successful":
            conditions.append("status IN ('ANSWER', 'Completed')")
            conditions.append("agent_number IN ('919656420060', '919188896915', '919037556420')")  # Only include known agents for successful calls
        elif status == "missed":
            conditions.append("(status NOT IN ('ANSWER', 'Completed') OR agent_number NOT IN ('919656420060', '919188896915', '919037556420') OR agent_number IS NULL)")  # Include both missed calls and calls without known agents
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    calls = frappe.db.sql("""
        SELECT 
            name,
            creation,
            agent_number,
            CASE 
                WHEN type = 'Incoming' THEN `from`
                WHEN type = 'Outgoing' THEN `to`
                ELSE NULL
            END as customer_number,
            status,
            duration,
            type,
            recording_url
        FROM 
            `tabVoxbay Call Log`
        WHERE 
            {where_clause}
        ORDER BY 
            creation DESC
        LIMIT 1000
    """.format(where_clause=where_clause), as_dict=1)
    
    # Add agent names and contact information to the data
    for call in calls:
        call['agent_name'] = get_agent_name(call['agent_number'])
        call['contact_info'] = get_contact_info(call['customer_number'])
    
    return calls

def get_context(context):
    context.no_cache = 1 