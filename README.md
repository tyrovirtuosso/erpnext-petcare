# ERPNext Petcare

A custom [Frappe/ERPNext](https://erpnext.com/) app for managing pet care services, grooming, customer engagement, and business automation.

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

## Usage

- Access pet care features from the ERPNext desk after installation.
- Configure scheduled jobs and integrations as needed.

## Development

- This app is designed for ERPNext v13+ and Frappe v13+.
- Contributions and suggestions are welcome!

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

**Maintainer:** [yourname](mailto:your@email.com)