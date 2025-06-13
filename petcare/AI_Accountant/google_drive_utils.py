import re
from google.oauth2 import service_account
from googleapiclient.discovery import build
from typing import Optional

# Service account JSON key path (reuse the same as in the test script)
SERVICE_ACCOUNT_FILE = "/home/frappe-user/frappe-bench/keys/trusty-catbird-422603-h3-9451d86c31ef.json"


def extract_file_id(drive_url_or_id: str) -> Optional[str]:
    """
    Extracts the file ID from a Google Drive URL or returns the input if it's already an ID.
    """
    # Google Drive file URL patterns
    patterns = [
        r"/d/([\w-]+)",  # /d/<id>
        r"id=([\w-]+)",  # id=<id>
        r"https://drive.google.com/open\?id=([\w-]+)",
        r"https://drive.google.com/file/d/([\w-]+)"
    ]
    for pattern in patterns:
        match = re.search(pattern, drive_url_or_id)
        if match:
            return match.group(1)
    # If no pattern matched, assume it's a file ID
    if re.match(r"^[\w-]{20,}$", drive_url_or_id):
        return drive_url_or_id
    return None


def authenticate_google_drive():
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/drive.metadata.readonly"]
    )
    return build("drive", "v3", credentials=credentials)


def get_drive_file_extension(drive_url_or_id: str) -> Optional[str]:
    """
    Given a Google Drive file URL or file ID, returns the file extension (e.g., 'pdf', 'docx').
    Returns None if not found or on error.
    """
    file_id = extract_file_id(drive_url_or_id)
    if not file_id:
        return None
    try:
        service = authenticate_google_drive()
        file = service.files().get(fileId=file_id, fields="id, name").execute()
        name = file.get("name", "")
        if "." in name:
            return name.split(".")[-1]
        return None
    except Exception:
        return None


def extract_folder_id(drive_url: str) -> Optional[str]:
    """
    Extracts the folder ID from a Google Drive folder URL.
    """
    match = re.search(r'/folders/([a-zA-Z0-9_-]+)', drive_url)
    if match:
        return match.group(1)
    return None


def list_files_in_folder(folder_id: str) -> list[dict]:
    """
    Lists all files in a Google Drive folder using the API.
    Returns a list of dicts with keys: id, name, mimeType.
    """
    service = authenticate_google_drive()
    query = f"'{folder_id}' in parents and trashed = false"
    results = service.files().list(q=query, fields="files(id, name, mimeType)").execute()
    return results.get('files', []) 