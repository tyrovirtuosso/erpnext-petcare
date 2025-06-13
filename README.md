# ERPNext Petcare

A custom [Frappe/ERPNext](https://erpnext.com/) app for managing pet care services, grooming, customer engagement, and business automation.

## Live Sites

- **Production:** [erp.masterpet.co.in](https://erp.masterpet.co.in)
- **Development:** [dev.masterpet.co.in](https://dev.masterpet.co.in)

## Features

- **Pet Grooming Management:** Track grooming reports, checklists, and photos.
- **Customer Engagement:** Tagging, loyalty programs, and automated service reminders.
- **Call Management:** Campaigns, call tasks, outcomes, and metrics for CRM-like workflows.
- **AI Accountant:** Automated journal entry creation using AI and Google Sheets/Drive integration:
  - Fetches transactions from Google Sheets
  - Processes invoices and documents from Google Drive
  - Uses AI to generate accurate journal entries
  - Automatically creates entries in ERPNext
  - Handles GST compliance and company-specific configurations
  - Includes OCR capabilities for invoice processing
- **Integrations:** Google Calendar, Google Sheets, Voxbay telephony, and more.
- **Automation:** Scheduled jobs for recurring service requests, customer updates, and loyalty calculations.
- **API Endpoints:** For service requests, messaging, and external integrations.

## Demo

### AI Accountant in Action
[![AI Accountant Demo](https://img.youtube.com/vi/je0u836lZHg/maxresdefault.jpg)](https://youtu.be/je0u836lZHg?si=poDj-4Ff7lum0mtA)

Watch how the AI Accountant automates the entire accounting workflow:
- Automated transaction fetching from Google Sheets
- Intelligent invoice processing with OCR
- AI-powered journal entry generation
- Seamless ERPNext integration
- GST-compliant accounting entries

### CI/CD Pipeline in Action
[![CI/CD Pipeline Demo](https://img.youtube.com/vi/BkBdrBQcXjs/maxresdefault.jpg)](https://youtu.be/BkBdrBQcXjs)

See our automated deployment pipeline in action:
- GitHub Actions workflow execution
- Automated deployment to development and production
- Zero-downtime updates
- Automatic backup creation
- Health checks and monitoring

### Voxbay Telephony Integration
[![Voxbay Integration Demo](https://img.youtube.com/vi/_W5jDjjMqxc/maxresdefault.jpg)](https://youtu.be/_W5jDjjMqxc)

Experience seamless telephony integration with ERPNext:
- Automatic call logging and tracking
- Real-time customer identification
- Call recording management
- Automated customer creation
- Detailed call analytics and reporting

#### API Integration
Our Voxbay integration uses a robust API system:
- Secure API key authentication
- Real-time webhook processing
- Automatic customer data synchronization
- Intelligent call status tracking
- Comprehensive error handling and logging

### Customer Location Map
[![Customer Location Map Demo](https://img.youtube.com/vi/LmUPbutaJa0/maxresdefault.jpg)](https://youtu.be/LmUPbutaJa0)

Interactive map visualization of customer locations with advanced features:
- Real-time customer location tracking
- Lead status-based filtering
- Cluster-based visualization
- Interactive customer information cards
- Territory-based grouping
- Service history integration

#### Key Features
- **Smart Clustering**: Automatically groups nearby customers for better visualization
- **Status-based Filtering**: Filter customers by lead status (New Lead, Interested, Converted, Lost)
- **Interactive Info Cards**: Quick access to customer details, service history, and contact information
- **Territory Management**: Visualize customer distribution across different territories
- **Service Tracking**: View days since last service and total pets for each customer
- **Facility Indicators**: Quick view of parking, electricity, and water availability

## Installation

1. Get the app:
    ```bash
    cd ~/frappe-bench/apps
    git clone https://github.com/yourusername/erpnext-petcare.git
    ```

2. Install the app on your site:
    ```bash
    bench --site yoursite install-app erpnext_petcare
    ```

3. Run migrations:
    ```bash
    bench --site yoursite migrate
    ```

## Development Workflow

We follow a `dev → main → production` workflow:

- **Development happens on** the `dev` branch, deployed to: [dev.masterpet.co.in](https://dev.masterpet.co.in)
- Once changes are tested and stable, they are merged into `main`
- **Production pulls only from** the `main` branch and is deployed to: [erp.masterpet.co.in](https://erp.masterpet.co.in)

### Steps:

1. **On dev server:**
    ```bash
    git checkout dev
    # Make changes
    bench --site dev.masterpet.co.in migrate
    bench restart
    git add .
    git commit -m "Your changes"
    git push origin dev
    ```

2. **To push to production:**
    ```bash
    git checkout main
    git merge dev
    git push origin main
    ```

3. **On prod server:**
    ```bash
    git pull origin main
    bench --site erp.masterpet.co.in migrate
    bench restart
    ```

### Updating Fields or Doctypes?

If you create or modify custom fields, Property Setters, or Doctypes in the dev site (`dev.masterpet.co.in`), you should export them so they can be version-controlled and applied on production.

1. **Export the changes as fixtures** (on dev):
    ```bash
    bench --site dev.masterpet.co.in export-fixtures --app erpnext_petcare
    ```

2. **Commit and push to the `dev` branch**:
    ```bash
    git add .
    git commit -m "Exported updated fixtures"
    git push origin dev
    ```

3. **Merge to `main` when tested**:
    ```bash
    git checkout main
    git merge dev
    git push origin main
    ```

4. **On production (`erp.masterpet.co.in`), pull and migrate**:
    ```bash
    git pull origin main
    bench --site erp.masterpet.co.in migrate
    bench restart
    ```

### Using `bench console` (Which Site?)

By default, running:

```bash
bench console
```
will open the console for the site defined in sites/common_site_config.json

To check which site you're in from inside the console:
```bash
frappe.local.site
```
This will return the active site name, like 'erp.masterpet.co.in' or 'dev.masterpet.co.in'.

✅ Best Practice
Always specify the site explicitly to avoid mistakes:

```bash
bench --site dev.masterpet.co.in console
bench --site erp.masterpet.co.in console
```

## Continuous Integration/Deployment (CI/CD)

Our project uses GitHub Actions for automated deployments to both development and production environments.

### 🚀 Automated Deployment Flow

- **Development Branch (`dev`)**: 
  - Automatically deploys to [dev.masterpet.co.in](https://dev.masterpet.co.in)
  - Triggered on every push to the `dev` branch

- **Production Branch (`main`)**: 
  - Automatically deploys to [erp.masterpet.co.in](https://erp.masterpet.co.in)
  - Triggered on every push to the `main` branch

### 🔧 How It Works

1. **GitHub Actions Workflow**
   - Located in `.github/workflows/deploy.yml`
   - Uses `appleboy/ssh-action` for secure SSH deployment
   - Triggers automatically on code pushes

2. **Server-Side Deployment Script**
   - Located at `~/frappe-bench/deploy.sh`
   - Handles the following tasks:
     - Pulls latest code from GitHub
     - Runs bench migrate and clears cache
     - Restarts necessary ERPNext services
     - Performs health checks
     - Logs all actions to deploy.log
     - Creates automatic backups before changes

3. **Security**
   - Passwordless automation using SSH keys
   - Configured sudoers for necessary commands
   - Secure handling of sensitive operations

### 📝 Deployment Logs

All deployment activities are logged to `~/frappe-bench/deploy.log` for monitoring and debugging purposes.

## Usage

- Access pet care features from the ERPNext desk after installation.
- Configure scheduled jobs and integrations as needed.

## Development

- This app is designed for ERPNext v13+ and Frappe v13+.
- Contributions and suggestions are welcome!

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

**Maintainer:** [Shane](mailto:shanejms2@gmail.com)