app_name = "upgrade_lens"
app_title = "Upgrade Lens"
app_publisher = "Open Source"
app_description = "Pre-migration upgrade assessment dashboard"
app_email = "dev@example.com"
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
