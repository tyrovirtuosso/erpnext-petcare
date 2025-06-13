import os
from .utils import get_openai_api_key, parse_amount
import instructor
import openai
from typing import List
from pydantic import BaseModel

class JournalEntryAccount(BaseModel):
    account: str
    debit_in_account_currency: float
    credit_in_account_currency: float
    user_remark: str

class JournalEntryAIResponse(BaseModel):
    accounts: List[JournalEntryAccount]
    title: str

def setup_openai():
    os.environ["OPENAI_API_KEY"] = get_openai_api_key()
    return instructor.from_openai(openai.OpenAI())

def generate_journal_entry_ai(transaction: dict, pdf_text: str, chart_of_accounts: list) -> dict:
    client = setup_openai()
    # Remove 'Account' key from transaction for the AI context
    filtered_transaction = {k: v for k, v in transaction.items() if k != "Account"}
    # Filter only non-group accounts for the AI context
    prompt = {
        "transaction": filtered_transaction,
        "pdf_text": pdf_text,
        "account_names": chart_of_accounts
    }
    response = client.chat.completions.create(
        model="o4-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert ERPNext accountant AI. "
                    "You are given the full chart of accounts (including group and non-group accounts) as context. "
                    "For each journal entry line, you must select the account using the exact `name` field of a non-group account (where `is_group` is 0). "
                    "Do NOT use `account_name`, do NOT use a parent or group account, do NOT use a colon-separated path, and do NOT invent or generalize names. "
                    "NEVER invent or guess account names. If you are unsure, return an error. "
                    "If the required account is not present in the provided list, return an error instead of inventing a name. "
                    "You must use only the exact string from the `name` field, e.g., `Architect Consulting Fees - MP`. "
                    "NEVER use a colon (:) in the account name. For example, `Professional Fees - MP:Architect Consulting Fees - MP` is INVALID. Only `Architect Consulting Fees - MP` is valid. "
                    "NEVER use any Creditors (Payable) accounts (such as 'Creditors - MP') in journal entries. If a transaction would normally use a Creditors account, instead use the appropriate bank, cash, or direct expense/income account. For example, do NOT use 'Creditors - MP' for supplier payments; use the bank account and the relevant expense account directly. If you are unsure, return an error. "
                    "If you are unsure which account to use, or if you cannot satisfy these rules, return an error message instead of journal entry lines. "
                    "Given the transaction details, generate a double-entry journal entry. "
                    "If there is a GST/tax component, split it out. Always include a bank account for the balancing entry. "
                    "Output a list of account entries (account, debit_in_account_currency, credit_in_account_currency, user_remark) and a title. "
                    "IMPORTANT: The total of all debit_in_account_currency values MUST EQUAL the total of all credit_in_account_currency values. "
                    "There MUST NOT be any row where both debit_in_account_currency and credit_in_account_currency are zero. "
                    "Do NOT use stock accounts (such as 'Stock In Hand - MP') in journal entries. These can only be updated via stock transactions in ERPNext. "
                    "If any account name contains a colon, or is not an exact match to a non-group account's `name`, return an error. "
                    "IMPORTANT: The total debit and total credit in the journal entry you generate must exactly match the value of the 'Withdrawal Amt (INR)' or 'Deposit Amt (INR)' field in the transaction (whichever is non-zero). Do not use any other value. "
                    "ADDITIONAL INSTRUCTION: When generating the journal entry, always ensure that the total debit and total credit exactly match the final invoice total (the amount after any rounding adjustments, typically labeled as 'TOTAL' or 'Grand Total' on the invoice). "
                    "If the invoice includes a 'Rounding Off' or similar adjustment, add a separate journal entry line for this amount using an appropriate 'Rounding Off' account. "
                    "The sum of all debits and credits, including any rounding adjustment, must exactly equal the final invoice total. "
                    "Do not use the sub-total or any amount before rounding as the journal entry total."
                )
            },
            {"role": "user", "content": str(prompt)}
        ],
        response_model=JournalEntryAIResponse
    )
    result = response.model_dump()
    # Post-processing validation
    accounts = result.get('accounts', [])
    total_debit = sum(a['debit_in_account_currency'] for a in accounts)
    total_credit = sum(a['credit_in_account_currency'] for a in accounts)
    zero_rows = [i+1 for i, a in enumerate(accounts) if a['debit_in_account_currency'] == 0 and a['credit_in_account_currency'] == 0]
    if zero_rows:
        raise ValueError(f"Invalid journal entry: Row(s) {zero_rows} have both debit and credit as zero. Please review the AI output.")

    return result