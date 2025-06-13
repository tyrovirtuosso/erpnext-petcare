from .invoice_insights import get_invoice_insights_for_transaction_id
import json

# Set your transaction ID here
TRANSACTION_ID = "S14391974"

def main():
    insights = get_invoice_insights_for_transaction_id(TRANSACTION_ID)
    if insights is not None:
        print("Extracted Invoice Insights for ERPNext Journal Entry:")
        print(insights.model_dump_json(indent=2))
    else:
        print(f"No invoice insights found for Tran. Id = {TRANSACTION_ID}.")

if __name__ == "__main__":
    main() 