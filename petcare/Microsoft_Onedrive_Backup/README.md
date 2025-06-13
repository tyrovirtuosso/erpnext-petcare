# ERPNext to OneDrive Backup

This script automates the backup of your ERPNext database and site configuration files to Microsoft OneDrive using the Microsoft Graph API.

## Features
- Uploads the latest ERPNext database backup (`*-database.sql.gz`) and site config backup (`*-site_config_backup.json`) to OneDrive.
- Organizes backups in OneDrive under `Backups/ERPNext/<timestamp>/` folders for easy retrieval and no redundancy.
- Uses Microsoft Graph API with secure authentication via environment variables.

## Prerequisites
- Python 3.8+
- ERPNext instance with regular backups enabled
- Microsoft Azure app registration with appropriate Graph API application permissions (`Files.ReadWrite.All`, `User.Read.All`)
- OneDrive account with sufficient storage

## Setup
1. **Clone or copy this script directory to your server.**
2. **Install dependencies:**
   ```bash
   pip install msal requests python-dotenv
   ```
3. **Create a `.env` file** in this directory with the following content:
   ```env
   CLIENT_ID=your_azure_app_client_id
   TENANT_ID=your_azure_tenant_id
   CLIENT_SECRET=your_azure_app_client_secret
   USER_ID=your_onedrive_user_email_or_id
   ```
4. **Ensure your ERPNext backups are stored in:**
   `/home/frappe-user/frappe-bench/sites/erp.masterpet.co.in/private/backups`

## Usage
Run the script manually:
```bash
python erpnext_onedrive_backup.py
```
- This will create a new folder in OneDrive with the current date and time, and upload the latest database and site config backups.

## Automation (Optional)
To run the backup automatically (e.g., daily at 1:00 AM), add a cron job:
```cron
0 1 * * * cd /home/frappe-user/frappe-bench/apps/petcare/petcare/Microsoft_Onedrive_Backup && /home/frappe-user/frappe-bench/env/bin/python erpnext_onedrive_backup.py
```

## Customization
- To upload additional file types (e.g., files tar, private files tar), modify the script's `get_latest_file` and upload logic.
- Change the backup directory or OneDrive folder structure as needed.

## Troubleshooting
- Ensure your Azure app has the correct permissions and admin consent is granted.
- Check the `.env` file for correct credentials.
- Review script output for error messages.

## License
MIT License 