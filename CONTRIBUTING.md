# Contributing to Upgrade Lens

Thank you for helping improve Upgrade Lens. This document covers local setup, expectations for changes, and how to submit work.

## Code of conduct

Be respectful and constructive. Focus on the technical merits of proposals and reviews.

## Getting started

1. **Fork** [frappe-upgrade-lens](https://github.com/usman8786/frappe-upgrade-lens) on GitHub.
2. **Clone** your fork into a Frappe bench:

   ```bash
   cd /path/to/frappe-bench
   git clone git@github.com:<your-username>/frappe-upgrade-lens.git apps/upgrade_lens
   ```

3. **Install** on a development site:

   ```bash
   bench --site <dev-site> install-app upgrade_lens
   cd apps/upgrade_lens/dashboard && yarn install && yarn build
   cd ../../.. && bench build --app upgrade_lens
   ```

4. Create a **feature branch** from `main`:

   ```bash
   git checkout -b feat/your-feature-name
   ```

## What to contribute

We welcome:

- Bug fixes and clearer error messages
- Additional upgrade rules (`config/rules/*.json`)
- Scanner improvements (deprecated APIs, new conflict checks)
- Dashboard UX and accessibility
- Documentation and tests

Please open an issue first for large features or breaking changes so we can align on approach.

## Coding standards

### Python

- Follow existing module layout under `upgrade_lens/`.
- Match Frappe conventions: tabs for indentation, `frappe._()` for user-facing strings.
- Keep scanners **read-only**—do not write to the database or modify files on disk.
- Administrator-only APIs must call `_require_administrator()` (or equivalent) before work runs.
- Run [Ruff](https://docs.astral.sh/ruff/) if you have it installed; settings are in `pyproject.toml`.

### Frontend

- Vue 3 components live in `dashboard/src/`.
- Use Frappe Desk styling patterns (`widget`, `indicator-pill`, `table-bordered`) for consistency.
- Import `__()` from `translate.js` in components that need translations.
- Rebuild after changes: `cd dashboard && yarn build`, then `bench build --app upgrade_lens`.

### Tests

- Add or update unit tests in `upgrade_lens/tests/unit/` for behavior you change.
- Mock `frappe` and external commands; unit tests should not require a live site.
- Run tests before opening a PR:

  ```bash
  cd apps/upgrade_lens
  /path/to/frappe-bench/env/bin/python -m unittest upgrade_lens.tests.unit.test_upgrade_lens -v
  ```

## Pull request checklist

- [ ] Branch is up to date with `main`
- [ ] Unit tests pass locally
- [ ] Dashboard rebuilt if UI changed (`yarn build` + `bench build --app upgrade_lens`)
- [ ] [CHANGELOG.md](CHANGELOG.md) updated under **Unreleased** (or release section if cutting a version)
- [ ] No unrelated formatting or drive-by refactors
- [ ] PR description explains **why** the change is needed and how to verify it

## Commit messages

Use clear, imperative subjects:

- `fix: detect uncommitted core hooks changes`
- `feat: add v16_to_v17 bundled rules`
- `docs: clarify optional site config keys`

## Reporting bugs

Include:

- Frappe / ERPNext versions
- Python, Node, and database versions
- Steps to reproduce
- Expected vs actual behavior
- Relevant scan output or screenshots (redact secrets)

Open a [GitHub issue](https://github.com/usman8786/frappe-upgrade-lens/issues) with the **Bug report** template when available.

## Questions

Use [GitHub Discussions](https://github.com/usman8786/frappe-upgrade-lens/discussions) or issues for questions that are not bug reports.

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
