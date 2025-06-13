import os
import json
from .utils import build_account_tree, get_chart_of_accounts as fetch_flat_accounts

CACHE_FILE = os.path.join(os.path.dirname(__file__), 'chart_of_accounts.json')

def load_chart_of_accounts():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    accounts = fetch_flat_accounts()  # fetch flat list
    chart = build_account_tree(accounts)  # build tree
    with open(CACHE_FILE, 'w') as f:
        json.dump(chart, f, indent=2)
    return chart