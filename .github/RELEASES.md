# Release process

This guide is for maintainers publishing [GitHub Releases](https://github.com/usman8786/frappe-upgrade-lens/releases) for Upgrade Lens.

## Versioning

We use [Semantic Versioning](https://semver.org/):

| Bump | When |
|------|------|
| **MAJOR** | Breaking API, removed scanners, incompatible Frappe version floor |
| **MINOR** | New scanners, rules, dashboard features, backward-compatible behavior |
| **PATCH** | Bug fixes, copy tweaks, dependency bumps with no behavior change |

Update version in both places before tagging:

- `upgrade_lens/__init__.py` → `__version__`
- `package.json` → `version` (build metadata)

## Pre-release checklist

1. All changes for the release are merged to `main`
2. [CHANGELOG.md](../CHANGELOG.md) has a dated section for the new version (move items out of **Unreleased**)
3. Unit tests pass:

   ```bash
   cd apps/upgrade_lens
   /path/to/frappe-bench/env/bin/python -m unittest upgrade_lens.tests.unit.test_upgrade_lens -v
   ```

4. Dashboard assets are built and committed (or built in CI before tag):

   ```bash
   cd dashboard && yarn install && yarn build
   cd ../../.. && bench build --app upgrade_lens
   ```

5. Confirm `upgrade_lens/public/dist/` is up to date if you commit built assets, or document that users must run `yarn build` after install

## Creating a release

```bash
# From apps/upgrade_lens on main
git pull origin main

# Commit version bumps + CHANGELOG if not already done
git add upgrade_lens/__init__.py package.json CHANGELOG.md
git commit -m "chore: release v0.0.2"

git tag -a v0.0.2 -m "v0.0.2"
git push origin main
git push origin v0.0.2
```

On GitHub:

1. Go to **Releases → Draft a new release**
2. Choose the tag (e.g. `v0.0.2`)
3. Title: `v0.0.2` (or a short descriptive title)
4. Paste the **## [0.0.2]** section from CHANGELOG.md as the release notes
5. Publish the release

## Release notes template

```markdown
## What's changed

- Bullet summary of user-visible changes

## Install / upgrade

\`\`\`bash
bench get-app https://github.com/usman8786/frappe-upgrade-lens --branch v0.0.2
bench --site <site> install-app upgrade_lens   # or migrate if already installed
cd apps/upgrade_lens/dashboard && yarn install && yarn build
bench build --app upgrade_lens
\`\`\`

## Full changelog

https://github.com/usman8786/frappe-upgrade-lens/blob/v0.0.2/CHANGELOG.md
```

## Hotfixes

For urgent fixes on the latest release:

1. Branch from the release tag: `git checkout -b hotfix/0.0.3 v0.0.2`
2. Fix, bump **PATCH** version, update CHANGELOG
3. Merge to `main`, tag `v0.0.3`, publish release

## Assets (optional)

GitHub release assets are optional for Frappe apps; users typically `bench get-app` from the tag or `main`. Do not attach secrets or site-specific configs.
