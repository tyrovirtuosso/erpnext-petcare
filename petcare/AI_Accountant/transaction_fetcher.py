from typing import Callable, List, Dict, Optional
from .utils import fetch_google_sheet_in_batches
from .config import SPREADSHEET_URL

def fetch_transactions_in_batches(
    sheet_name: str,
    batch_size: int,
    filter_fn: Optional[Callable[[Dict], bool]] = None,
    spreadsheet_url: str = None,
    exclude_columns: Optional[list] = None
):
    """
    Fetch transactions from Google Sheet in batches, applying an optional filter function.
    Yields lists of transactions (dicts).
    """
    spreadsheet_url = spreadsheet_url or SPREADSHEET_URL
    for batch in fetch_google_sheet_in_batches(sheet_name, spreadsheet_url=spreadsheet_url, batch_size=batch_size):
        filtered_batch = []
        for tx in batch:
            tx_filtered = {k: v for k, v in tx.items() if k not in exclude_columns}
            if not filter_fn or filter_fn(tx_filtered):
                filtered_batch.append(tx_filtered)
        if filtered_batch:
            yield filtered_batch