# Upgrade Lens

Standalone Frappe app for read-only pre-migration upgrade assessments.

## Features

- Upgrade Matrix Dashboard (Desk Page, Administrator only)
- System environment and database metrics
- Official app git upstream drift detection
- Client/Server Script deprecated pattern scan
- Custom field conflict detection
- Migration strategy planner (in-place, staging-first, clean server)

## Install (temporary test on a bench)

```bash
cd /path/to/frappe-bench
bench get-app <your-repo-url>  # or copy apps/upgrade_lens
bench --site <site> install-app upgrade_lens
cd apps/upgrade_lens/dashboard && yarn install
cd ../.. && bench build --app upgrade_lens
bench --site <site> migrate
```

Open Desk → **Upgrade Lens** → `/app/upgrade-matrix-dashboard`

## Uninstall (safe removal)

```bash
bench --site <site> uninstall-app upgrade_lens --yes --no-backup
bench --site <site> console  # frappe.cache.delete_keys("upgrade_lens:*")
rm -rf apps/upgrade_lens
```

## Development

```bash
cd apps/upgrade_lens/dashboard && yarn install && yarn build
cd ../.. && python -m pytest upgrade_lens/tests/unit/
```

## Site config (optional)

```json
{
  "upgrade_lens_rules_url": "https://raw.githubusercontent.com/.../v15_to_v16.json",
  "upgrade_lens_git_fetch_enabled": true,
  "upgrade_lens_git_fetch_cache_hours": 24
}
```

## Isolation

This app does not modify `react_platform`, ERPNext core, or production data. All scanners are read-only.
