# Changelog

All notable changes to Upgrade Lens are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Open-source documentation: README, CONTRIBUTING, release process, MIT license

## [0.0.1] - 2025-06-23

### Added

- **Upgrade Matrix Dashboard** — Desk page (`/app/upgrade-matrix-dashboard`) for Administrator users
- **Environment scanner** — Python, Node.js, and database version checks against target Frappe release rules
- **Database metrics** — Table counts and size signals for migration planning
- **Installed apps audit** — Versions, remotes, and git upstream drift for official Frappe ecosystem apps
- **Code scanner** — Deprecated pattern detection in Client Scripts and Server Scripts
- **Conflict detection** — Custom app hooks, custom field conflicts, and core app file modifications
- **Strategy planner** — Risk scoring with six migration paths (A–F) and a single recommended route
- **Hybrid rules engine** — Site config override, GitHub fetch, and bundled JSON rules with Redis cache
- **Vue 3 dashboard** — Vite-built IIFE bundle with KPI header, compatibility grid, and tabbed scanner views
- **Unit tests** — Core strategist, git audit, and rules behavior

[Unreleased]: https://github.com/usman8786/frappe-upgrade-lens/compare/v0.0.1...HEAD
[0.0.1]: https://github.com/usman8786/frappe-upgrade-lens/releases/tag/v0.0.1
