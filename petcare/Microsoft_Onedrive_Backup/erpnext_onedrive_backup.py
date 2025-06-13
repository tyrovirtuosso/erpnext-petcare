import os
import glob
import requests
from msal import ConfidentialClientApplication
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
TENANT_ID = os.getenv("TENANT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
USER_ID = os.getenv("USER_ID")
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPE = ["https://graph.microsoft.com/.default"]

# ERPNext backup directory (existing backups)
BACKUP_DIR = "/home/frappe-user/frappe-bench/sites/erp.masterpet.co.in/private/backups"


def get_latest_file(pattern):
    files = sorted(
        glob.glob(os.path.join(BACKUP_DIR, pattern)),
        key=os.path.getmtime,
        reverse=True
    )
    if not files:
        print(f"No files found for pattern: {pattern}")
        return None
    return files[0]


def get_access_token():
    app = ConfidentialClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        client_credential=CLIENT_SECRET
    )
    result = app.acquire_token_for_client(scopes=SCOPE)
    if "access_token" not in result:
        print("Failed to get access token:", result)
        return None
    return result["access_token"]


def ensure_onedrive_folder(headers, folder_path):
    url = f"https://graph.microsoft.com/v1.0/users/{USER_ID}/drive/root:/{folder_path}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()["id"]
    # Create folder
    parent_path = "/".join(folder_path.strip("/").split("/")[:-1])
    folder_name = folder_path.strip("/").split("/")[-1]
    parent_url = (
        f"https://graph.microsoft.com/v1.0/users/{USER_ID}/drive/root:/{parent_path}:/children"
        if parent_path else
        f"https://graph.microsoft.com/v1.0/users/{USER_ID}/drive/root/children"
    )
    data = {
        "name": folder_name,
        "folder": {},
        "@microsoft.graph.conflictBehavior": "fail"  # fail if exists
    }
    response = requests.post(parent_url, headers=headers, json=data)
    if response.status_code in (200, 201):
        return response.json()["id"]
    elif response.status_code == 409:
        # Folder already exists, get its id
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()["id"]
    print("Failed to create/find folder:", response.text)
    return None


def upload_file_to_onedrive(headers, folder_path, file_path):
    file_name = os.path.basename(file_path)
    upload_url = f"https://graph.microsoft.com/v1.0/users/{USER_ID}/drive/root:/{folder_path}/{file_name}:/content"
    with open(file_path, "rb") as f:
        response = requests.put(upload_url, headers=headers, data=f)
    if response.status_code in (200, 201):
        print(f"Backup uploaded successfully as {file_name}")
        return True
    print(f"Failed to upload {file_name}:", response.text)
    return False


def main():
    access_token = get_access_token()
    if not access_token:
        return
    headers = {"Authorization": f"Bearer {access_token}"}
    base_folder_path = "Backups/ERPNext"
    # Ensure base folder exists
    base_folder_id = ensure_onedrive_folder(headers, base_folder_path)
    if not base_folder_id:
        return
    # Create a new subfolder with current date and time
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    dated_folder_path = f"{base_folder_path}/{timestamp}"
    dated_folder_id = ensure_onedrive_folder(headers, dated_folder_path)
    if not dated_folder_id:
        return
    # Upload latest database backup
    db_backup = get_latest_file("*-database.sql.gz")
    if db_backup:
        upload_file_to_onedrive(headers, dated_folder_path, db_backup)
    # Upload latest site config backup
    config_backup = get_latest_file("*-site_config_backup.json")
    if config_backup:
        upload_file_to_onedrive(headers, dated_folder_path, config_backup)


if __name__ == "__main__":
    main() 
    
#    python erpnext_onedrive_backup.py