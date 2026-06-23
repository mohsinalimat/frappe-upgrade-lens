## What's changed

<!-- Copy highlights from CHANGELOG.md for this version -->

-

## Install / upgrade

```bash
bench get-app https://github.com/usman8786/frappe-upgrade-lens --branch vX.Y.Z
bench --site <site> install-app upgrade_lens
cd apps/upgrade_lens/dashboard && yarn install && yarn build
bench build --app upgrade_lens
bench --site <site> migrate
```

## Full changelog

https://github.com/usman8786/frappe-upgrade-lens/blob/vX.Y.Z/CHANGELOG.md
