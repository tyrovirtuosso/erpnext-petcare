import frappe
from datetime import datetime
import os
from fpdf import FPDF

def get_output_dir():
    """Get the directory where this script is located"""
    # Get the absolute path of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return script_dir

class PDF(FPDF):
    def header(self):
        # Arial bold 15
        self.set_font('Arial', 'B', 15)
        # Title
        self.cell(0, 10, 'Service Request and Sales Invoice Mismatch Analysis', 0, 1, 'C')
        # Line break
        self.ln(10)

    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # Arial italic 8
        self.set_font('Arial', 'I', 8)
        # Page number
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def check_mismatches():
    """Simple script to check mismatches between Service Requests and Sales Invoices"""
    
    # Get output directory (same as script directory)
    output_dir = get_output_dir()
    
    # Create timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    txt_filename = os.path.join(output_dir, f"sr_invoice_mismatch_{timestamp}.txt")
    pdf_filename = os.path.join(output_dir, f"sr_invoice_mismatch_{timestamp}.pdf")
    
    # Get all customers with completed service requests - only check status
    customers = frappe.db.sql("""
        SELECT DISTINCT customer 
        FROM `tabService Request` 
        WHERE customer IS NOT NULL 
        AND status = 'Completed'
    """, as_dict=1)

    # Calculate all totals first
    total_customers = len(customers)
    total_service_requests = 0
    total_sales_invoices = 0
    customers_with_mismatch = 0
    
    # Pre-calculate totals
    for customer_dict in customers:
        customer = customer_dict.customer
        sr_count = frappe.db.count('Service Request', {
            'customer': customer,
            'status': 'Completed'
        })
        si_count = frappe.db.count('Sales Invoice', {
            'customer': customer,
            'docstatus': 1,
            'is_return': 0
        })
        total_service_requests += sr_count
        total_sales_invoices += si_count
        if sr_count != si_count:
            customers_with_mismatch += 1
    
    # Create PDF
    pdf = PDF()
    pdf.add_page()
    
    # Write to both files
    with open(txt_filename, 'w') as f:
        # Write headers
        header = "Service Request and Sales Invoice Mismatch Analysis\n"
        subheader = f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        f.write(header)
        f.write(subheader)
        
        # Write summary at the beginning
        summary = f"""Summary:
--------
Total Customers with Completed Service Requests: {total_customers}
Total Completed Service Requests: {total_service_requests}
Total Sales Invoices: {total_sales_invoices}
Customers with Mismatches: {customers_with_mismatch}

Detailed Analysis:
-----------------
"""
        f.write(summary)
        
        # Write summary to PDF at the beginning
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 10, subheader, 0, 1)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, "Summary", 0, 1)
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 8, f"Total Customers with Completed Service Requests: {total_customers}", 0, 1)
        pdf.cell(0, 8, f"Total Completed Service Requests: {total_service_requests}", 0, 1)
        pdf.cell(0, 8, f"Total Sales Invoices: {total_sales_invoices}", 0, 1)
        pdf.cell(0, 8, f"Customers with Mismatches: {customers_with_mismatch}", 0, 1)
        pdf.ln(10)
        
        # Add detailed analysis header to PDF
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, "Detailed Analysis", 0, 1)
        pdf.set_font('Arial', '', 10)
        
        # Process each customer for detailed analysis
        for customer_dict in customers:
            customer = customer_dict.customer
            
            # Count completed service requests - only check status
            sr_count = frappe.db.count('Service Request', {
                'customer': customer,
                'status': 'Completed'
            })
            
            # Count sales invoices - keep docstatus=1 for invoices as they should be submitted
            si_count = frappe.db.count('Sales Invoice', {
                'customer': customer,
                'docstatus': 1,
                'is_return': 0
            })
            
            difference = sr_count - si_count
            customer_name = frappe.db.get_value('Customer', customer, 'customer_name')
            
            # Format the line
            line = f"{customer:<15} | {customer_name:<30} | {sr_count:>10} | {si_count:>10} | {difference:>10}\n"
            
            # Write to text file
            if difference != 0:  # Only write mismatches to keep the report focused
                f.write(line)
                
                # Write to PDF
                pdf.cell(0, 6, f"Customer: {customer} ({customer_name})", 0, 1)
                pdf.cell(0, 6, f"Service Requests: {sr_count} | Sales Invoices: {si_count} | Difference: {difference}", 0, 1)
                
                # List Service Requests without invoices if there's a positive difference
                if difference > 0:
                    f.write("\nPending Service Requests:\n")
                    pdf.cell(0, 6, "Pending Service Requests:", 0, 1)
                    
                    service_requests = frappe.get_all('Service Request', 
                        filters={
                            'customer': customer,
                            'status': 'Completed',
                            'sales_invoice': ['is', 'not set']
                        },
                        fields=['name', 'creation']
                    )
                    for sr in service_requests:
                        sr_line = f"  - {sr.name} (Created: {sr.creation.date()})\n"
                        f.write(sr_line)
                        pdf.cell(0, 6, f"  {sr.name} (Created: {sr.creation.date()})", 0, 1)
                
                f.write("\n" + "-" * 80 + "\n")
                pdf.ln(5)
    
    # Save PDF
    pdf.output(pdf_filename)
    
    print(f"\nAnalysis complete!")
    print(f"Text report saved to: {txt_filename}")
    print(f"PDF report saved to: {pdf_filename}")
    return txt_filename, pdf_filename

# to run the script, use the following command:
# from petcare.petcare.scripts.service_request_analysis.check_sr_invoice_mismatch import check_mismatches
# check_mismatches()
