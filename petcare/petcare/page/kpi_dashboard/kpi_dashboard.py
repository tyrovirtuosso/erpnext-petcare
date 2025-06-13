# Placeholder for KPI Dashboard backend logic 

import frappe
from frappe import _

@frappe.whitelist()
def get_revenue(from_date, to_date, prev_from_date=None, prev_to_date=None):
    def get_totals(start, end):
        invoices = frappe.get_all(
            "Sales Invoice",
            filters={
                "status": "Paid",
                "posting_date": ["between", [start, end]]
            },
            fields=["grand_total", "net_total"]
        )
        grand_total = sum(inv["grand_total"] for inv in invoices)
        net_total = sum(inv["net_total"] for inv in invoices)
        return {"grand_total": grand_total, "net_total": net_total}

    current = get_totals(from_date, to_date)
    previous = get_totals(prev_from_date, prev_to_date) if prev_from_date and prev_to_date else {"grand_total": 0, "net_total": 0}
    return {
        "current": current,
        "previous": previous
    } 

@frappe.whitelist()
def get_customer_count():
    """Get count of customers who have at least one completed service request"""
    # Get all service requests that are completed
    completed_requests = frappe.get_all(
        "Service Request",
        filters={
            "status": "Completed"
        },
        fields=["customer"]
    )
    
    # Get unique customers from completed requests
    unique_customers = set(request["customer"] for request in completed_requests)
    
    return {
        "total_customers": len(unique_customers)
    } 
    
@frappe.whitelist()
def get_customer_growth():
    """Get customer growth month by month based on first completed service"""
    # Get all completed service requests with their dates
    completed_requests = frappe.get_all(
        "Service Request",
        filters={
            "status": "Completed"
        },
        fields=["customer", "completed_date"]
    )
    
    # Dictionary to store first completed service date for each customer
    customer_first_service = {}
    
    # Find the first completed service date for each customer
    for request in completed_requests:
        customer = request["customer"]
        completed_date = request["completed_date"]
        
        if customer not in customer_first_service or completed_date < customer_first_service[customer]:
            customer_first_service[customer] = completed_date
    
    # Group customers by month of their first service
    monthly_growth = {}
    for customer, first_date in customer_first_service.items():
        # Format date as YYYY-MM for grouping
        month_key = first_date.strftime("%Y-%m")
        if month_key not in monthly_growth:
            monthly_growth[month_key] = 0
        monthly_growth[month_key] += 1
    
    # Sort months chronologically
    sorted_months = sorted(monthly_growth.items())
    
    # Calculate cumulative growth
    cumulative_customers = 0
    growth_data = []
    
    for month, new_customers in sorted_months:
        cumulative_customers += new_customers
        growth_data.append({
            "month": month,
            "new_customers": new_customers,
            "total_customers": cumulative_customers
        })
    
    return {
        "growth_data": growth_data,
        "total_customers": cumulative_customers
    }

@frappe.whitelist()
def get_monthly_revenue():
    """Get monthly revenue from completed service requests"""
    # Get all completed service requests with their amounts and dates
    completed_requests = frappe.get_all(
        "Service Request",
        filters={
            "status": "Completed"
        },
        fields=["amount_after_discount", "completed_date"]
    )
    
    # Group revenue by month
    monthly_revenue = {}
    
    for request in completed_requests:
        # Format date as YYYY-MM for grouping
        month_key = request["completed_date"].strftime("%Y-%m")
        amount = request["amount_after_discount"] or 0
        
        if month_key not in monthly_revenue:
            monthly_revenue[month_key] = 0
        monthly_revenue[month_key] += amount
    
    # Sort months chronologically
    sorted_months = sorted(monthly_revenue.items())
    
    # Calculate cumulative revenue
    cumulative_revenue = 0
    revenue_data = []
    
    for month, revenue in sorted_months:
        cumulative_revenue += revenue
        revenue_data.append({
            "month": month,
            "monthly_revenue": revenue,
            "cumulative_revenue": cumulative_revenue
        })
    
    return {
        "revenue_data": revenue_data,
        "total_revenue": cumulative_revenue
    }

@frappe.whitelist()
def get_arpu():
    """Calculate Average Revenue Per User (ARPU)"""
    # Get all completed service requests with their amounts and customers
    completed_requests = frappe.get_all(
        "Service Request",
        filters={
            "status": "Completed"
        },
        fields=["customer", "amount_after_discount"]
    )
    
    # Calculate total revenue
    total_revenue = sum(request["amount_after_discount"] or 0 for request in completed_requests)
    
    # Get unique customers
    unique_customers = set(request["customer"] for request in completed_requests)
    total_customers = len(unique_customers)
    
    # Calculate ARPU
    arpu = total_revenue / total_customers if total_customers > 0 else 0
    
    return {
        "total_revenue": total_revenue,
        "total_customers": total_customers,
        "arpu": arpu,
        "arpu_formatted": f"₹{arpu:,.2f}"
    }

@frappe.whitelist()
def get_monthly_arpu():
    """Calculate Average Revenue Per User (ARPU) for each month"""
    # Get all completed service requests with their amounts, customers and dates
    completed_requests = frappe.get_all(
        "Service Request",
        filters={
            "status": "Completed"
        },
        fields=["customer", "amount_after_discount", "completed_date"]
    )
    
    # Group requests by month
    monthly_data = {}
    
    for request in completed_requests:
        month_key = request["completed_date"].strftime("%Y-%m")
        amount = request["amount_after_discount"] or 0
        customer = request["customer"]
        
        if month_key not in monthly_data:
            monthly_data[month_key] = {
                "revenue": 0,
                "customers": set()
            }
        
        monthly_data[month_key]["revenue"] += amount
        monthly_data[month_key]["customers"].add(customer)
    
    # Calculate ARPU for each month
    arpu_data = []
    for month, data in sorted(monthly_data.items()):
        num_customers = len(data["customers"])
        arpu = data["revenue"] / num_customers if num_customers > 0 else 0
        
        arpu_data.append({
            "month": month,
            "revenue": data["revenue"],
            "revenue_formatted": f"₹{data['revenue']:,.2f}",
            "customers": num_customers,
            "arpu": arpu,
            "arpu_formatted": f"₹{arpu:,.2f}"
        })
    
    return {
        "monthly_arpu": arpu_data
    }

@frappe.whitelist()
def get_top_customers(limit=10):
    """Get top customers by total revenue from completed service requests"""
    # Get all completed service requests with their amounts and customers
    completed_requests = frappe.get_all(
        "Service Request",
        filters={
            "status": "Completed"
        },
        fields=["customer", "amount_after_discount", "customer_name"]
    )
    
    # Calculate total revenue per customer
    customer_revenue = {}
    for request in completed_requests:
        customer = request["customer"]
        amount = request["amount_after_discount"] or 0
        customer_name = request["customer_name"]
        
        if customer not in customer_revenue:
            customer_revenue[customer] = {
                "name": customer_name,
                "total_revenue": 0,
                "service_count": 0
            }
        
        customer_revenue[customer]["total_revenue"] += amount
        customer_revenue[customer]["service_count"] += 1
    
    # Sort customers by revenue and get top 10
    sorted_customers = sorted(
        customer_revenue.items(),
        key=lambda x: x[1]["total_revenue"],
        reverse=True
    )[:limit]
    
    # Format the results
    top_customers = []
    for customer, data in sorted_customers:
        top_customers.append({
            "customer": customer,
            "customer_name": data["name"],
            "total_revenue": data["total_revenue"],
            "total_revenue_formatted": f"₹{data['total_revenue']:,.2f}",
            "service_count": data["service_count"],
            "average_revenue": data["total_revenue"] / data["service_count"],
            "average_revenue_formatted": f"₹{(data['total_revenue'] / data['service_count']):,.2f}"
        })
    
    return {
        "top_customers": top_customers
    }

@frappe.whitelist()
def get_top_customers_by_services(limit=10):
    """Get top customers by number of completed service requests"""
    # Get all completed service requests with their customers
    completed_requests = frappe.get_all(
        "Service Request",
        filters={
            "status": "Completed"
        },
        fields=["customer", "customer_name", "amount_after_discount"]
    )
    
    # Count services and calculate revenue per customer
    customer_services = {}
    for request in completed_requests:
        customer = request["customer"]
        amount = request["amount_after_discount"] or 0
        
        if customer not in customer_services:
            customer_services[customer] = {
                "name": request["customer_name"],
                "service_count": 0,
                "total_revenue": 0
            }
        
        customer_services[customer]["service_count"] += 1
        customer_services[customer]["total_revenue"] += amount
    
    # Sort customers by service count and get top 10
    sorted_customers = sorted(
        customer_services.items(),
        key=lambda x: x[1]["service_count"],
        reverse=True
    )[:limit]
    
    # Format the results
    top_customers = []
    for customer, data in sorted_customers:
        top_customers.append({
            "customer": customer,
            "customer_name": data["name"],
            "service_count": data["service_count"],
            "total_revenue": data["total_revenue"],
            "total_revenue_formatted": f"₹{data['total_revenue']:,.2f}",
            "average_revenue": data["total_revenue"] / data["service_count"],
            "average_revenue_formatted": f"₹{(data['total_revenue'] / data['service_count']):,.2f}"
        })
    
    return {
        "top_customers": top_customers
    }

@frappe.whitelist()
def get_pet_breed_stats():
    """Get statistics about pet breeds from customers with converted service requests"""
    # First get all customers with converted service requests
    converted_customers = frappe.get_all(
        "Service Request",
        filters={
            "status": "Completed"
        },
        fields=["customer"]
    )
    
    # Get unique customer IDs
    customer_ids = set(request["customer"] for request in converted_customers)
    
    # Get all pets from these customers
    breed_stats = {}
    total_pets = 0
    
    for customer_id in customer_ids:
        # Get customer's pets
        customer_pets = frappe.get_all(
            "Pet Child Table",
            filters={
                "parent": customer_id,
                "parenttype": "Customer"
            },
            fields=["breed_name"]
        )
        # Count breeds
        for pet in customer_pets:
            breed = pet["breed_name"]
            if breed:
                if breed not in breed_stats:
                    breed_stats[breed] = 0
                breed_stats[breed] += 1
                total_pets += 1
    
    # Sort breeds by count
    sorted_breeds = sorted(
        breed_stats.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    # Format the results
    breed_data = []
    for breed, count in sorted_breeds:
        percentage = (count / total_pets * 100) if total_pets > 0 else 0
        breed_data.append({
            "breed": breed,
            "count": count,
            "percentage": percentage,
            "percentage_formatted": f"{percentage:.1f}%"
        })
    
    return {
        "breed_stats": breed_data,
        "total_pets": total_pets,
        "total_breeds": len(breed_stats)
    }

@frappe.whitelist()
def get_territory_stats():
    """Get statistics about customer territories from completed service requests"""
    # First get all customers with completed service requests
    completed_requests = frappe.get_all(
        "Service Request",
        filters={
            "status": "Completed"
        },
        fields=["customer"]
    )
    
    # Get unique customer IDs
    customer_ids = set(request["customer"] for request in completed_requests)
    
    # Get territory information for these customers
    territory_stats = {}
    total_customers = 0
    
    for customer_id in customer_ids:
        # Get customer's territory
        customer = frappe.get_doc("Customer", customer_id)
        territory = customer.territory
        
        if territory:
            if territory not in territory_stats:
                territory_stats[territory] = {
                    "customer_count": 0,
                    "revenue": 0
                }
            territory_stats[territory]["customer_count"] += 1
            total_customers += 1
    
    # Get revenue for each territory
    for territory in territory_stats:
        territory_customers = frappe.get_all(
            "Customer",
            filters={
                "territory": territory,
                "name": ["in", list(customer_ids)]
            },
            fields=["name"]
        )
        
        # Get revenue from completed service requests for these customers
        for customer in territory_customers:
            customer_requests = frappe.get_all(
                "Service Request",
                filters={
                    "customer": customer.name,
                    "status": "Completed"
                },
                fields=["amount_after_discount"]
            )
            
            territory_revenue = sum(request["amount_after_discount"] or 0 for request in customer_requests)
            territory_stats[territory]["revenue"] += territory_revenue
    
    # Sort territories by customer count
    sorted_territories = sorted(
        territory_stats.items(),
        key=lambda x: x[1]["customer_count"],
        reverse=True
    )
    
    # Format the results
    territory_data = []
    for territory, stats in sorted_territories:
        percentage = (stats["customer_count"] / total_customers * 100) if total_customers > 0 else 0
        territory_data.append({
            "territory": territory,
            "customer_count": stats["customer_count"],
            "percentage": percentage,
            "percentage_formatted": f"{percentage:.1f}%",
            "revenue": stats["revenue"],
            "revenue_formatted": f"₹{stats['revenue']:,.2f}",
            "average_revenue": stats["revenue"] / stats["customer_count"] if stats["customer_count"] > 0 else 0,
            "average_revenue_formatted": f"₹{(stats['revenue'] / stats['customer_count']):,.2f}" if stats["customer_count"] > 0 else "₹0.00"
        })
    
    return {
        "territory_stats": territory_data,
        "total_customers": total_customers,
        "total_territories": len(territory_stats)
    }

@frappe.whitelist()
def get_cohort_analysis():
    """Cohort analysis: rows are cohort months, columns are months since cohort, values are list of customers (id, name) from that cohort active in that month"""
    import datetime
    from collections import defaultdict
    
    # Step 1: Fetch all completed service requests
    completed_requests = frappe.get_all(
        "Service Request",
        filters={"status": "Completed"},
        fields=["customer", "customer_name", "completed_date"]
    )
    
    # Step 2: For each customer, find cohort month and all active months
    customer_first_month = {}
    customer_active_months = defaultdict(set)
    customer_names = {}
    for req in completed_requests:
        customer = req["customer"]
        customer_name = req.get("customer_name")
        date = req["completed_date"]
        if not date:
            continue
        month = date.strftime("%Y-%m")
        # Track first month
        if customer not in customer_first_month or month < customer_first_month[customer]:
            customer_first_month[customer] = month
        # Track all active months
        customer_active_months[customer].add(month)
        # Track name
        if customer_name:
            customer_names[customer] = customer_name
    
    # Step 3: Build cohort matrix (set of customer ids for each cell)
    cohort_matrix = defaultdict(lambda: defaultdict(set))
    for customer, cohort_month in customer_first_month.items():
        cohort_date = datetime.datetime.strptime(cohort_month, "%Y-%m")
        for active_month in customer_active_months[customer]:
            active_date = datetime.datetime.strptime(active_month, "%Y-%m")
            offset = (active_date.year - cohort_date.year) * 12 + (active_date.month - cohort_date.month)
            if offset >= 0:
                cohort_matrix[cohort_month][offset].add(customer)
    
    # Step 4: Format as nested dict (cohort_month -> offset -> list of {id, name})
    cohort_result = {}
    for cohort_month in sorted(cohort_matrix.keys()):
        cohort_result[cohort_month] = {}
        for offset in sorted(cohort_matrix[cohort_month].keys()):
            cohort_result[cohort_month][offset] = [
                {"id": cid, "name": customer_names.get(cid, "")} for cid in sorted(cohort_matrix[cohort_month][offset])
            ]
    
    return {"cohort": cohort_result}

@frappe.whitelist()
def get_customer_funnel():
    """Get customer funnel analysis showing progression through different stages"""
    from datetime import datetime, timedelta, date
    
    # Get all customers
    all_customers = frappe.get_all(
        "Customer",
        fields=["name"]
    )
    
    # Get all completed service requests
    completed_requests = frappe.get_all(
        "Service Request",
        filters={
            "status": "Completed"
        },
        fields=["customer", "completed_date"]
    )
    
    # Calculate different customer segments
    customer_service_count = {}
    customer_last_service = {}
    
    for request in completed_requests:
        customer = request["customer"]
        completed_date = request["completed_date"]
        
        # Count services per customer
        if customer not in customer_service_count:
            customer_service_count[customer] = 0
        customer_service_count[customer] += 1
        
        # Track last service date
        if customer not in customer_last_service or completed_date > customer_last_service[customer]:
            customer_last_service[customer] = completed_date
    
    # Calculate metrics
    prospects = len(all_customers) - len(customer_service_count)  # Customers with no service requests
    first_time_customers = len(customer_service_count)  # Customers with at least one service
    returning_customers = len([c for c, count in customer_service_count.items() if count > 1])  # More than one service
    regular_customers = len([c for c, count in customer_service_count.items() if count > 2])  # More than two services
    
    # Calculate active customers (last 30 days)
    thirty_days_ago = date.today() - timedelta(days=30)
    active_customers = len([
        c for c, last_date in customer_last_service.items()
        if last_date >= thirty_days_ago
    ])
    
    # Calculate stage-to-stage conversion rates
    prospect_to_first_time_rate = (first_time_customers / prospects * 100) if prospects > 0 else 0
    first_time_to_returning_rate = (returning_customers / first_time_customers * 100) if first_time_customers > 0 else 0
    returning_to_regular_rate = (regular_customers / returning_customers * 100) if returning_customers > 0 else 0
    regular_to_active_rate = (active_customers / regular_customers * 100) if regular_customers > 0 else 0
    
    return {
        "funnel": {
            "prospects": prospects,
            "first_time": first_time_customers,
            "returning": returning_customers,
            "regular": regular_customers,
            "active": active_customers
        },
        "rates": {
            "prospect_to_first_time": round(prospect_to_first_time_rate, 2),
            "first_time_to_returning": round(first_time_to_returning_rate, 2),
            "returning_to_regular": round(returning_to_regular_rate, 2),
            "regular_to_active": round(regular_to_active_rate, 2)
        },
        "formatted": {
            "prospects": f"{prospects:,}",
            "first_time": f"{first_time_customers:,}",
            "returning": f"{returning_customers:,}",
            "regular": f"{regular_customers:,}",
            "active": f"{active_customers:,}",
            "prospect_to_first_time": f"{prospect_to_first_time_rate:.1f}%",
            "first_time_to_returning": f"{first_time_to_returning_rate:.1f}%",
            "returning_to_regular": f"{returning_to_regular_rate:.1f}%",
            "regular_to_active": f"{regular_to_active_rate:.1f}%"
        }
    }

'''
from petcare.petcare.page.kpi_dashboard.kpi_dashboard import get_customer_count
result = get_customer_count()
print(f"Total customers with completed service requests: {result['total_customers']}")
'''