app_name = "upgrade_lens"
app_title = "Upgrade Lens"
app_publisher = "Upgrade Lens Contributors"
app_description = "Read-only pre-migration upgrade assessment dashboard for Frappe"
app_email = "https://github.com/usman8786/frappe-upgrade-lens"
app_license = "mit"

# Standalone app — no required_apps, fixtures, patches, doc_events, or global JS.

add_to_apps_screen = [
	{
		"name": "upgrade_lens",
		"logo": "/assets/upgrade_lens/images/upgrade_lens.svg",
		"title": "Upgrade Lens",
		"route": "/app/upgrade-matrix-dashboard",
	}
]
