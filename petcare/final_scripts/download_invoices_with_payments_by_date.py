import frappe
import os
import logging
from datetime import datetime
from tqdm import tqdm



def download_invoices_with_payments_by_date():
    """
    1. Fetch all submitted Sales Invoices (docstatus=1).
    2. For each invoice:
       - Build a folder path: Sales_Invoices/<year>/<month>/<day>/<invoice_name>.
       - Check if the PDF for the invoice already exists; if not, generate it.
       - Fetch related Payment Entries (docstatus=1 only) and do the same.
    3. Use "GST Tax Invoice" + "Masterpet Letter Head" for Sales Invoices.
       Use "Bank and Cash Payment" + "Masterpet Letter Head" for Payment Entries.
    4. Show a console progress bar for Sales Invoices.
    5. Suppress WeasyPrint logs so CSS warnings do not appear.
    """

    logging.disable(logging.CRITICAL)

    # Optionally force language to "en" if desired
    old_lang = frappe.local.lang
    try:
        frappe.local.lang = "en"

        base_path = "/home/frappe-user/frappe-bench/Sales_Invoices"

        # Fetch all submitted Sales Invoices (docstatus=1)
        invoices = frappe.get_list(
            "Sales Invoice",
            filters={"docstatus": 1},
            fields=["name", "docstatus", "posting_date"]
        )
        total_invoices = len(invoices)
        print("Number of submitted invoices:", total_invoices)

        # Loop over Invoices with a progress bar
        for inv in tqdm(invoices, desc="Processing Invoices", unit="invoice"):
            # Ensure posting_date is available
            if not inv.posting_date:
                continue

            year_str = inv.posting_date.strftime("%Y")
            month_str = inv.posting_date.strftime("%m")
            day_str = inv.posting_date.strftime("%d")

            date_folder = os.path.join(base_path, year_str, month_str, day_str)
            os.makedirs(date_folder, exist_ok=True)

            invoice_folder = os.path.join(date_folder, inv.name)
            os.makedirs(invoice_folder, exist_ok=True)

            # --- Generate Sales Invoice PDF (if not already present) ---
            invoice_pdf_path = os.path.join(invoice_folder, f"{inv.name}.pdf")
            if not os.path.exists(invoice_pdf_path):
                invoice_pdf_data = frappe.get_print(
                    doctype="Sales Invoice",
                    name=inv.name,
                    print_format="GST Tax Invoice",       # <--- Use your GST print format
                    letterhead="Masterpet Letter Head",    # <--- Use your letter head
                    as_pdf=True
                )
                with open(invoice_pdf_path, "wb") as f:
                    f.write(invoice_pdf_data)

            # --- Fetch related Payment Entries (docstatus=1 only) ---
            payment_refs = frappe.get_all(
                "Payment Entry Reference",
                filters={
                    "reference_doctype": "Sales Invoice",
                    "reference_name": inv.name
                },
                fields=["parent"]
            )
            pe_names = [ref.parent for ref in payment_refs]

            payment_entries = frappe.get_all(
                "Payment Entry",
                filters={
                    "name": ("in", pe_names),
                    "docstatus": 1  # Only submitted Payment Entries
                },
                fields=["name"]
            )

            # --- Generate PDFs for Payment Entries ---
            for pe in payment_entries:
                payment_pdf_path = os.path.join(invoice_folder, f"{pe.name}.pdf")
                if not os.path.exists(payment_pdf_path):
                    payment_pdf_data = frappe.get_print(
                        doctype="Payment Entry",
                        name=pe.name,
                        print_format="Bank and Cash Payment",  # <--- Use your Payment Entry format
                        letterhead="Masterpet Letter Head",     # <--- Use your letter head
                        as_pdf=True
                    )
                    with open(payment_pdf_path, "wb") as f:
                        f.write(payment_pdf_data)

            # Print a final message (tqdm shows the progress bar separately)
            # print(f"Processed Sales Invoice: {inv.name} in {invoice_folder}")

    finally:
        # Restore original language
        frappe.local.lang = old_lang
        logging.disable(logging.NOTSET)
        
'''
from petcare.final_scripts.download_invoices_with_payments_by_date import download_invoices_with_payments_by_date
download_invoices_with_payments_by_date()
'''