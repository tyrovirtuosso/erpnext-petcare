import frappe
from typing import List, Dict, Optional
import os
import json
from .gsheet_utils import get_sheet_data, format_gsheet_date
from datetime import datetime
import sys

# Open output file for writing (overwrite each run)
output_file_path = os.path.join(os.path.dirname(__file__), "output.txt")
output_file = open(output_file_path, "w")

def get_gl_entries(account: str, from_date: Optional[str] = None, to_date: Optional[str] = None, company: Optional[str] = None) -> List[Dict]:
    """
    Fetch GL Entries for a given account and optional date range.
    Only fetches required fields and only submitted entries (docstatus=1).
    Filters by company if provided.
    After fetching, attaches cheque_no or reference_no from parent document for reference-based matching.
    """
    filters = {"account": account, "docstatus": 1}
    if company:
        filters["company"] = company
    if from_date and to_date:
        filters["posting_date"] = ["between", [from_date, to_date]]
    entries = frappe.get_all(
        "GL Entry",
        filters=filters,
        fields=[
            "posting_date",
            "account",
            "voucher_type",
            "voucher_subtype",
            "debit",
            "credit",
            "against",
            "voucher_no"
        ],
        order_by="posting_date asc, name asc"
    )
    # Attach cheque_no or reference_no from parent document
    for entry in entries:
        vt = entry.get("voucher_type", "")
        if vt == "Journal Entry":
            entry["cheque_no"] = frappe.get_value("Journal Entry", entry["voucher_no"], "cheque_no")
        # Attach reference_no for any Payment Entry (case-insensitive, substring match)
        if "payment" in vt.lower():
            entry["reference_no"] = frappe.get_value("Payment Entry", entry["voucher_no"], "reference_no")
        else:
            entry["cheque_no"] = entry.get("cheque_no", None)
            entry["reference_no"] = entry.get("reference_no", None)
    return entries


def calculate_balances(entries: List[Dict]) -> List[Dict]:
    """
    Add running balance to each entry.
    """
    balance = 0
    for entry in entries:
        balance += (entry.get("debit") or 0) - (entry.get("credit") or 0)
        entry["balance"] = balance
    return entries


def print_entries_with_balance(entries: List[Dict]) -> None:
    """
    Print entries in a readable tabular format with running balance.
    Only prints required fields.
    """
    header = (
        f"{'Date':<12} | {'Account':<20} | {'Voucher Type':<14} | {'Voucher Subtype':<14} | {'Debit':>12} | {'Credit':>12} | {'Balance':>14} | {'Against Account':<20} | {'Voucher No':<18}"
    )
    print(header)
    print("-" * len(header))
    for entry in entries:
        # Format the date as YYYY-MM-DD
        date_str = str(entry.get('posting_date', ''))
        if ' ' in date_str:
            date_str = date_str.split(' ')[0]
        print(
            f"{date_str:<12} | {entry['account']:<20} | {entry.get('voucher_type',''):<14} | {entry.get('voucher_subtype',''):<14} | {entry.get('debit',0):>12,.2f} | {entry.get('credit',0):>12,.2f} | {entry['balance']:>14,.2f} | {str(entry.get('against') or ''):<20} | {str(entry.get('voucher_no') or ''):<18}"
        )


def filter_by_date(entries, date_key, from_date, to_date):
    """Filter a list of dicts by date range (inclusive)."""
    if not from_date and not to_date:
        return entries
    filtered = []
    for entry in entries:
        date_str = entry.get(date_key)
        if not date_str:
            continue
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        except Exception:
            continue
        if from_date and date_obj < datetime.strptime(from_date, "%Y-%m-%d"):
            continue
        if to_date and date_obj > datetime.strptime(to_date, "%Y-%m-%d"):
            continue
        filtered.append(entry)
    return filtered


def clean_amount(val):
    try:
        return float(str(val).replace(',', '').strip() or 0)
    except Exception:
        return 0.0


def fetch_gsheet_transactions(from_date=None, to_date=None):
    """Fetch and filter Google Sheet transactions by date (using 'Transaction Date')."""
    rows = get_sheet_data()
    txns = []
    for row in rows:
        date = format_gsheet_date(row.get("Transaction Date", ""))
        txn = {
            "tran_id": row.get("Tran. Id"),
            "date": date,
            "withdrawal": clean_amount(row.get("Withdrawal Amt (INR)", "0")),
            "deposit": clean_amount(row.get("Deposit Amt (INR)", "0")),
            "balance": clean_amount(row.get("Balance (INR)", "0")),
        }
        if date:
            txns.append(txn)
    return filter_by_date(txns, "date", from_date, to_date)


def get_parent_docstatus_map(voucher_type, voucher_nos):
    """Return a dict mapping voucher_no to docstatus for the given voucher_type."""
    if not voucher_nos:
        return {}
    doctype = None
    if voucher_type == "Journal Entry":
        doctype = "Journal Entry"
    elif voucher_type == "Payment Entry":
        doctype = "Payment Entry"
    elif voucher_type == "Sales Invoice":
        doctype = "Sales Invoice"
    else:
        doctype = voucher_type
    if not doctype:
        return {}
    docs = frappe.get_all(
        doctype,
        filters={"name": ["in", list(voucher_nos)]},
        fields=["name", "docstatus"]
    )
    return {d["name"]: d["docstatus"] for d in docs}


def filter_gl_entries_by_parent_docstatus(gl_entries):
    """Filter GL entries to only those whose parent docstatus is 1 (submitted)."""
    # Group by voucher_type
    from collections import defaultdict
    vt_to_vnos = defaultdict(set)
    for entry in gl_entries:
        vt_to_vnos[entry["voucher_type"]].add(entry["voucher_no"])
    # Build a map of (voucher_type, voucher_no) -> docstatus
    vt_vno_to_docstatus = {}
    for vt, vnos in vt_to_vnos.items():
        vno_to_docstatus = get_parent_docstatus_map(vt, vnos)
        for vno, ds in vno_to_docstatus.items():
            vt_vno_to_docstatus[(vt, vno)] = ds
    # Filter
    filtered = [
        entry for entry in gl_entries
        if vt_vno_to_docstatus.get((entry["voucher_type"], entry["voucher_no"])) == 1
    ]
    return filtered


def fetch_erp_entries_with_balance(account, from_date=None, to_date=None, company=None):
    entries = get_gl_entries(account, from_date, to_date, company)
    # Filter by parent docstatus
    entries = filter_gl_entries_by_parent_docstatus(entries)
    entries_with_balance = calculate_balances(entries)
    erp_entries = []
    for entry in entries_with_balance:
        date_str = str(entry["posting_date"])
        if " " in date_str:
            date_str = date_str.split(" ")[0]
        erp_entries.append({
            "date": date_str,
            "debit": entry.get("debit", 0),
            "credit": entry.get("credit", 0),
            "balance": entry.get("balance", 0),
            "voucher_no": entry.get("voucher_no"),
            "voucher_type": entry.get("voucher_type"),
            "cheque_no": entry.get("cheque_no"),
            "reference_no": entry.get("reference_no"),
        })
    return filter_by_date(erp_entries, "date", from_date, to_date)


def compare_and_print(gsheet_txns, erp_entries):
    output_file.write(f"{'Tran. Id':<12} | {'Date':<12} | {'Withdrawal':>12} | {'Deposit':>12} | {'GS Balance':>12} || {'ERP Debit':>12} | {'ERP Credit':>12} | {'ERP Balance':>12} | {'Voucher No':<18} | Status\n")
    output_file.write("-" * 130 + "\n")
    unmatched_erp_entries = erp_entries.copy()
    erp_running_balance = 0.0
    for txn in gsheet_txns:
        is_deposit = (txn.get("deposit") or 0) > 0
        is_withdrawal = (txn.get("withdrawal") or 0) > 0
        # Find all unmatched ERP entries whose reference/cheque_no contains the tran_id
        matching_erp_entries = []
        for idx, e in enumerate(unmatched_erp_entries):
            ref_match = False
            if e["voucher_type"] == "Journal Entry":
                ref_val = e.get("cheque_no")
                ref_match = ref_val and (str(txn["tran_id"]) in str(ref_val))
            elif e["voucher_type"] == "Payment Entry" or ("payment" in str(e.get("voucher_type", "")).lower()):
                ref_val = e.get("reference_no")
                ref_match = ref_val and (str(txn["tran_id"]) in str(ref_val))
            # Only match the correct direction for the bank account
            if ref_match:
                if is_deposit and e.get("debit", 0) > 0:
                    matching_erp_entries.append((idx, e))
                elif is_withdrawal and e.get("credit", 0) > 0:
                    matching_erp_entries.append((idx, e))
        # Sum debits and credits
        total_debit = sum(e.get("debit", 0) for _, e in matching_erp_entries)
        total_credit = sum(e.get("credit", 0) for _, e in matching_erp_entries)
        match = False
        voucher_nos = []
        if is_deposit and abs(total_debit - txn["deposit"]) < 0.01:
            match = True
            voucher_nos = [e["voucher_no"] for _, e in matching_erp_entries]
        elif is_withdrawal and abs(total_credit - txn["withdrawal"]) < 0.01:
            match = True
            voucher_nos = [e["voucher_no"] for _, e in matching_erp_entries]
        # Output
        status = "Match" if match else "Missing in ERP"
        erp_debit_str = f"{total_debit:,.2f}" if match and is_deposit else ""
        erp_credit_str = f"{total_credit:,.2f}" if match and is_withdrawal else ""
        voucher_no_str = ", ".join(voucher_nos) if match else ""
        # Update ERP running balance for matched entries
        erp_balance = ""
        if match:
            # Remove all matched ERP entries from unmatched_erp_entries and update running balance
            for idx, e in sorted(matching_erp_entries, reverse=True):
                erp_running_balance += (e.get("debit", 0) or 0) - (e.get("credit", 0) or 0)
                unmatched_erp_entries.pop(idx)
            erp_balance = f"{erp_running_balance:,.2f}"
        # Remove color codes for file output
        status_colored = status
        output_file.write(f"{txn['tran_id']:<12} | {txn['date']:<12} | {txn['withdrawal']:>12,.2f} | {txn['deposit']:>12,.2f} | {txn['balance']:>12,.2f} || {erp_debit_str:>12} | {erp_credit_str:>12} | {erp_balance:>12} | {voucher_no_str:<18} | {status_colored}\n")
    # Print unmatched ERP entries
    for e in unmatched_erp_entries:
        erp_debit_str = f"{e['debit']:,.2f}" if isinstance(e['debit'], (int, float)) and e['debit'] != "" else ""
        erp_credit_str = f"{e['credit']:,.2f}" if isinstance(e['credit'], (int, float)) and e['credit'] != "" else ""
        erp_running_balance += (e['debit'] or 0) - (e['credit'] or 0)
        erp_balance_str = f"{erp_running_balance:,.2f}" if isinstance(erp_running_balance, (int, float)) else ""
        status_colored = "Missing in Sheet"
        output_file.write(f"{'':<12} | {e['date']:<12} | {'':>12} | {'':>12} | {'':>12} || {erp_debit_str:>12} | {erp_credit_str:>12} | {erp_balance_str:>12} | {e['voucher_no']:<18} | {status_colored}\n")
    output_file.flush()


def main():
    """
    Main function for bench execute. Reads account, company, from_date, to_date from config.json.
    Also fetches and compares Google Sheet transactions.
    """
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    if not os.path.exists(config_path):
        print(f"Config file not found: {config_path}")
        return

    with open(config_path, "r") as f:
        config = json.load(f)

    account = config.get("account")
    company = config.get("company")
    from_date = config.get("from_date")
    to_date = config.get("to_date")

    if not account:
        print("Error: 'account' parameter is required in config.json.")
        return

    # Fetch and compare
    gsheet_txns = fetch_gsheet_transactions(from_date, to_date)
    erp_entries = fetch_erp_entries_with_balance(account, from_date, to_date, company)
    compare_and_print(gsheet_txns, erp_entries)

#  bench execute petcare.final_scripts.bank_erp_mismatch_detector.bank_erp_mismatch_detector.main

