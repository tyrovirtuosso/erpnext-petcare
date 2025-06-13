import os
import pytest
from msal import ConfidentialClientApplication
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
TENANT_ID = os.getenv("TENANT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPE = ["https://graph.microsoft.com/.default"]
USER_ID = os.getenv("USER_ID")

@pytest.mark.one_drive
def test_onedrive_access():
    # Authenticate
    app = ConfidentialClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        client_credential=CLIENT_SECRET
    )
    result = app.acquire_token_for_client(scopes=SCOPE)
    assert "access_token" in result, f"Failed to get token: {result}"

    # Call OneDrive API
    headers = {"Authorization": f"Bearer {result['access_token']}"}
    response = requests.get(
        f"https://graph.microsoft.com/v1.0/users/{USER_ID}/drive/root/children",
        headers=headers
    )
    assert response.status_code == 200, f"API call failed: {response.text}"
    data = response.json()
    assert "value" in data, "No files found in OneDrive root"
    print("OneDrive root files:", data["value"])