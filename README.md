# Upgrade Lens

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Upgrade Lens** is a standalone [Frappe](https://frappeframework.com) app that gives you a read-only, pre-migration upgrade assessment from the Desk. Scan your bench environment, installed apps, customizations, and infrastructure compatibility—then get a ranked migration strategy before you touch production.

> **Read-only by design.** Upgrade Lens does not modify your database, core apps, or site data. All scanners inspect the current state and report findings.

## Features

| Area | What it checks |
|------|----------------|
| **Environment** | Python, Node.js, database version vs target Frappe release requirements |
| **Database metrics** | Table counts, largest tables, DocType volume signals |
| **Installed apps** | Versions, git remotes, upstream drift for official Frappe/ERPNext apps |
| **Code scanner** | Deprecated patterns in Client Scripts and Server Scripts |
| **Customizations** | Custom app hooks, custom field conflicts, core file modifications |
| **Strategy planner** | Risk score plus six migration paths (A–F) with one recommended route |

The dashboard is available at **Desk → Upgrade Lens** (`/app/upgrade-matrix-dashboard`). Access is limited to the **Administrator** role.

## Requirements

- [Frappe Bench](https://github.com/frappe/bench) with Frappe **v15+** (developed and tested on v16)
- Python 3.10+
- Node.js 18+ (for building the dashboard assets)
- Yarn

## Installation

```bash
cd /path/to/frappe-bench

# From GitHub
bench get-app https://github.com/usman8786/frappe-upgrade-lens

# Or clone manually into apps/
# git clone https://github.com/usman8786/frappe-upgrade-lens.git apps/upgrade_lens

bench --site <your-site> install-app upgrade_lens

cd apps/upgrade_lens/dashboard && yarn install && yarn build
cd ../../.. && bench build --app upgrade_lens
bench --site <your-site> migrate
```

Open **Desk → Upgrade Lens** or navigate to `/app/upgrade-matrix-dashboard`.

## Uninstall

```bash
bench --site <your-site> uninstall-app upgrade_lens --yes --no-backup
```

Optional cache cleanup:

```bash
bench --site <your-site> console
```

```python
import frappe
frappe.cache.delete_keys("upgrade_lens:*")
```

Remove the app directory if you cloned it manually:

```bash
rm -rf apps/upgrade_lens
```

## Configuration (optional)

Add these keys to your site `site_config.json` or **Site Config** in Desk:

| Key | Description | Default |
|-----|-------------|---------|
| `upgrade_lens_rules_url` | URL to a custom rules JSON file | Bundled rules in `config/rules/` |
| `upgrade_lens_git_fetch_enabled` | Fetch upstream git tags during scans | `true` |
| `upgrade_lens_git_fetch_cache_hours` | Hours to cache git fetch results | `24` |

Example:

```json
{
  "upgrade_lens_rules_url": "https://raw.githubusercontent.com/your-org/your-rules/main/v16_to_v17.json",
  "upgrade_lens_git_fetch_enabled": true,
  "upgrade_lens_git_fetch_cache_hours": 24
}
```

## Development

```bash
# Build dashboard after UI changes
cd apps/upgrade_lens/dashboard && yarn install && yarn build

# Rebuild Frappe assets
cd ../../.. && bench build --app upgrade_lens

# Run unit tests (from bench root, with env activated)
cd apps/upgrade_lens
/path/to/frappe-bench/env/bin/python -m unittest upgrade_lens.tests.unit.test_upgrade_lens -v
```

### Project layout

```
upgrade_lens/
├── dashboard/          # Vue 3 + Vite Desk UI
├── upgrade_lens/
│   ├── api/            # scanner, rules, conflicts, strategist
│   ├── utils/          # git audit, DB metrics, version helpers
│   ├── config/         # app registry and bundled upgrade rules
│   └── tests/          # unit tests
├── LICENSE
├── CONTRIBUTING.md
└── CHANGELOG.md
```

## Migration paths

The strategy planner evaluates six paths and recommends exactly one based on your scan:

| Path | Name | Typical use |
|------|------|-------------|
| **A** | In-place upgrade | Low risk, infra compatible, few customizations |
| **B** | Staging-first | Validate on a copy before production |
| **C** | Clean server | Infrastructure fails compatibility (e.g. unsupported Python) |
| **D** | Staging + remediation | Custom scripts or hooks need fixes before upgrade |
| **E** | DB housekeeping | Large or noisy database; cleanup before migration |
| **F** | Core reconciliation | Uncommitted or diverged changes in core apps |

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, coding standards, and the pull request process.

## Releases

Version history and release notes are in [CHANGELOG.md](CHANGELOG.md). Maintainers: see [.github/RELEASES.md](.github/RELEASES.md) for tagging and publishing.

## License

This project is licensed under the [MIT License](LICENSE).
