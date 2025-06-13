app_name = "petcare"
app_title = "Petcare"
app_publisher = "sj"
app_description = "Petcare modules"
app_email = "sjsj.cloud@gmail.com"
app_license = "mit"

# Scheduler Reference Guide
# -----------------------

# 1. How to create a new scheduled job in console:
"""
import frappe
doc = frappe.get_doc({
    'doctype': 'Scheduled Job Type',
    'method': 'petcare.scripts.scheduler_events.daily_customer_service_update',
    'frequency': 'Cron',
    'cron_format': '30 21 * * *',  # Runs at 3:00 AM IST (21:30 UTC)
    'status': 'Active',
    'docstatus': 0
})
doc.insert()
frappe.db.commit()
"""

# 2. How to check all active PetCare scheduled jobs in console:
"""
import frappe
jobs = frappe.get_all('Scheduled Job Type', 
    filters=[
        ['stopped', '=', 0],
        ['method', 'like', '%petcare%']
    ],
    fields=['method', 'frequency', 'cron_format', 'last_execution']
)
for job in jobs:
    print(f"\nMethod: {job.method}")
    print(f"Frequency: {job.frequency}")
    print(f"Cron Format: {job.cron_format}")
    print(f"Last Execution: {job.last_execution}")
"""

doc_events = {}
override_whitelisted_methods = {}
override_doctype_class = {}

scheduler_events = {
    "cron": {
        "0 4 * * *": [  # This cron expression runs the task every day at 4:00 AM
            "petcare.scripts.generate_recurring_service_requests.generate_recurring_service_requests"
        ],
        "0 3 * * *": [
            "petcare.scripts.update_customer_service_details.update_customer_service_details"
        ]
    }
}

doc_events = {
    "Service Request": {
        "on_update": "petcare.scripts.service_request_hooks.update_latest_completed_service",
        "on_submit": "petcare.scripts.loyalty.update_loyalty_totals",
        "before_save": "petcare.scripts.loyalty.update_loyalty_totals",
    },
    "Customer": {
        "before_save": "petcare.scripts.update_customer_coordinates.update_single_customer_coordinates"
    },
    "Call Task": {
        "on_update": "petcare.api.call_task.call_task.on_update"
    }
}

permission_query_conditions = {
    "Contact": "petcare.scripts.contact_permissions.get_contact_permission_query"
}
    
has_whitelisted_web_request = True



# doc_events = {
#     "Contact": {
#         "after_save": "petcare.scripts.contact_hooks.update_customer_mobile_no"
#     }
# }


# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "petcare",
# 		"logo": "/assets/petcare/logo.png",
# 		"title": "Petcare",
# 		"route": "/petcare",
# 		"has_permission": "petcare.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/petcare/css/petcare.css"
# app_include_js = "/assets/petcare/js/petcare.js"

# include js, css files in header of web template
# web_include_js = "/assets/petcare/js/petcare.js"
# web_include_css = "/assets/petcare/css/petcare.css"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "petcare/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "petcare/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "petcare.utils.jinja_methods",
# 	"filters": "petcare.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "petcare.install.before_install"
# after_install = "petcare.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "petcare.uninstall.before_uninstall"
# after_uninstall = "petcare.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "petcare.utils.before_app_install"
# after_app_install = "petcare.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "petcare.utils.before_app_uninstall"
# after_app_uninstall = "petcare.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "petcare.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

#Scheduled Tasks
#---------------

# scheduler_events = {
#     "daily": [
#         "petcare.scripts.generate_recurring_service_requests.generate_recurring_service_requests"
#     ]
# }



# scheduler_events = {
# 	# "all": [
# 	# 	"petcare.tasks.all"
# 	# ],
# 	"daily": [
# 		"petcare.scripts.generate_recurring_service_requests.generate_recurring_service_requests"
# 	],
# 	# "hourly": [
# 	# 	"petcare.tasks.hourly"
# 	# ],
# 	# "weekly": [
# 	# 	"petcare.tasks.weekly"
# 	# ],
# 	# "monthly": [
# 	# 	"petcare.tasks.monthly"
# 	# ],
# }

# Testing
# -------

# before_tests = "petcare.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "petcare.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "petcare.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["petcare.utils.before_request"]
# after_request = ["petcare.utils.after_request"]

# Job Events
# ----------
# before_job = ["petcare.utils.before_job"]
# after_job = ["petcare.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"petcare.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

