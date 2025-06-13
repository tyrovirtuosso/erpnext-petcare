# ERPNext Petcare

A custom [Frappe/ERPNext](https://erpnext.com/) app for managing pet care services, grooming, customer engagement, and business automation.

## Live Sites

- **Production:** [erp.masterpet.co.in](https://erp.masterpet.co.in)
- **Development:** [dev.masterpet.co.in](https://dev.masterpet.co.in)

## Features

- **Pet Grooming Management:** Track grooming reports, checklists, and photos.
- **Customer Engagement:** Tagging, loyalty programs, and automated service reminders.
- **Call Management:** Campaigns, call tasks, outcomes, and metrics for CRM-like workflows.
- **Integrations:** Google Calendar, Google Sheets, Voxbay telephony, and more.
- **Automation:** Scheduled jobs for recurring service requests, customer updates, and loyalty calculations.
- **API Endpoints:** For service requests, messaging, and external integrations.

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