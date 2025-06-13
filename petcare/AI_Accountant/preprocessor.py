import os
import tempfile
import requests
import re
from .utils import check_journal_entry_by_cheque_no, format_transaction_date, extract_pdf_text, extract_drive_file_id, download_drive_pdf, get_drive_file_extension_util, extract_text_from_drive_file, IMAGE_EXTENSIONS, clean_invoice_text
from .google_drive_utils import extract_folder_id, list_files_in_folder

def download_pdf_from_url(url: str) -> str:
    response = requests.get(url)
    response.raise_for_status()
    fd, path = tempfile.mkstemp(suffix='.pdf')
    with os.fdopen(fd, 'wb') as tmp:
        tmp.write(response.content)
    return path

def split_links(links: str) -> list[str]:
    # Split by comma, newline, or both, and strip whitespace
    return [l.strip() for l in re.split(r'[,\n]+', links) if l.strip()]

def get_invoice_pdf_text(transaction: dict) -> tuple[str | None, list[dict]]:
    links = transaction.get("Links to Invoice")
    if not links:
        return None, []
    link_list = split_links(links)
    extracted_texts = []
    link_summaries = []
    for link in link_list:
        folder_id = extract_folder_id(link)
        if folder_id:
            # It's a folder link, list and process all files
            files = list_files_in_folder(folder_id)
            for file in files:
                file_link = f"https://drive.google.com/file/d/{file['id']}/view"
                ext = get_drive_file_extension_util(file_link).lower()
                if ext == "pdf":
                    file_id = file['id']
                    pdf_path = f"invoice_{transaction.get('Tran. Id')}_{len(extracted_texts)}.pdf"
                    if not download_drive_pdf(file_id, pdf_path):
                        continue
                    pdf_text = extract_pdf_text(pdf_path)
                    cleaned_text = clean_invoice_text(pdf_text)
                    os.remove(pdf_path)
                    extracted_texts.append(cleaned_text)
                    link_summaries.append({
                        "type": ext,
                        "file": file_link,
                        "status": "success"
                    })
                elif ext == "csv":
                    file_id = file['id']
                    csv_path = f"invoice_{transaction.get('Tran. Id')}_{len(extracted_texts)}.csv"
                    if not download_drive_pdf(file_id, csv_path):
                        continue
                    try:
                        with open(csv_path, 'r', encoding='utf-8') as f:
                            csv_text = f.read()
                        extracted_texts.append(csv_text.strip())
                        link_summaries.append({
                            "type": ext,
                            "file": file_link,
                            "status": "success"
                        })
                    except Exception as e:
                        print(f"ERROR: Could not read CSV for Tran. Id {transaction.get('Tran. Id', 'N/A')} (file: {csv_path}): {e}")
                        link_summaries.append({
                            "type": ext,
                            "file": file_link,
                            "status": "error",
                            "error": str(e)
                        })
                    finally:
                        os.remove(csv_path)
                elif ext in IMAGE_EXTENSIONS:
                    extracted_texts.append(extract_text_from_drive_file(file_link))
                    link_summaries.append({
                        "type": ext,
                        "file": file_link,
                        "status": "success"
                    })
                else:
                    continue
        else:
            # Not a folder, process as single file
            ext = get_drive_file_extension_util(link).lower()
            if ext == "pdf":
                file_id = extract_drive_file_id(link)
                pdf_path = f"invoice_{transaction.get('Tran. Id')}_{len(extracted_texts)}.pdf"
                if not download_drive_pdf(file_id, pdf_path):
                    continue
                pdf_text = extract_pdf_text(pdf_path)
                cleaned_text = clean_invoice_text(pdf_text)
                os.remove(pdf_path)
                extracted_texts.append(cleaned_text)
                link_summaries.append({
                    "type": ext,
                    "file": link,
                    "status": "success"
                })
            elif ext == "csv":
                file_id = extract_drive_file_id(link)
                csv_path = f"invoice_{transaction.get('Tran. Id')}_{len(extracted_texts)}.csv"
                if not download_drive_pdf(file_id, csv_path):
                    continue
                try:
                    with open(csv_path, 'r', encoding='utf-8') as f:
                        csv_text = f.read()
                    extracted_texts.append(csv_text.strip())
                    link_summaries.append({
                        "type": ext,
                        "file": link,
                        "status": "success"
                    })
                except Exception as e:
                    print(f"ERROR: Could not read CSV for Tran. Id {transaction.get('Tran. Id', 'N/A')} (file: {csv_path}): {e}")
                    link_summaries.append({
                        "type": ext,
                        "file": link,
                        "status": "error",
                        "error": str(e)
                    })
                finally:
                    os.remove(csv_path)
            elif ext in IMAGE_EXTENSIONS:
                extracted_texts.append(extract_text_from_drive_file(link))
                link_summaries.append({
                    "type": ext,
                    "file": link,
                    "status": "success"
                })
            else:
                continue
    if extracted_texts:
        return ("\n\n".join(extracted_texts), link_summaries)
    return None, []

def preprocess_transaction(transaction: dict, skip_if_docstatus: list = [1]) -> dict:
    """
    Checks for existing journal entry with specified docstatus, formats date, and extracts PDF text if needed.
    Returns dict with keys: 'skip', 'reason', 'transaction', 'pdf_text'.
    """
    tran_id = transaction.get('Tran. Id')
    if not tran_id:
        return {'skip': True, 'reason': 'Missing Tran. Id', 'transaction': transaction, 'pdf_text': None}
    entries = check_journal_entry_by_cheque_no(tran_id)
    if any(e['docstatus'] in skip_if_docstatus for e in entries):
        return {'skip': True, 'reason': f"Journal entry exists with docstatus in {skip_if_docstatus}", 'transaction': transaction, 'pdf_text': None}
    transaction['Transaction Date'] = format_transaction_date(transaction.get('Transaction Date', ''))
    pdf_text, link_summaries = get_invoice_pdf_text(transaction)
    return {'skip': False, 'reason': None, 'transaction': transaction, 'pdf_text': pdf_text, 'link_summaries': link_summaries} 