"""Load upgrade rules from site config, remote GitHub, or bundled JSON."""

from __future__ import annotations

import json
from pathlib import Path

import frappe
import requests

from upgrade_lens.utils.version import major_version

CACHE_KEY_PREFIX = "upgrade_lens:rules:"
RULES_REPO_BASE = "https://raw.githubusercontent.com/frappe/upgrade-lens-rules/main"
REQUEST_TIMEOUT = 30


def _require_administrator() -> None:
	if frappe.session.user != "Administrator":
		frappe.throw(
			frappe._("Only Administrator can access upgrade rules."),
			frappe.PermissionError,
		)


def _cache_key(source_major: int, target_major: int) -> str:
	return f"{CACHE_KEY_PREFIX}{source_major}:{target_major}"


def _bundled_rules_path(source_major: int, target_major: int) -> Path:
	return Path(
		frappe.get_app_path(
			"upgrade_lens",
			"config",
			"rules",
			f"v{source_major}_to_v{target_major}.json",
		)
	)


def _load_bundled_rules(source_major: int, target_major: int) -> dict | None:
	path = _bundled_rules_path(source_major, target_major)
	if not path.exists():
		return None
	return json.loads(path.read_text(encoding="utf-8"))


def _fetch_remote_rules(url: str) -> dict | None:
	try:
		response = requests.get(url, timeout=REQUEST_TIMEOUT)
		response.raise_for_status()
		return response.json()
	except Exception as exc:
		frappe.log_error(title="upgrade_lens rules fetch failed", message=f"{url}\n{exc}")
		return None


def _default_remote_url(source_major: int, target_major: int) -> str:
	return f"{RULES_REPO_BASE}/v{source_major}_to_v{target_major}.json"


def get_rules(source_major: int | str, target_major: int | str) -> dict:
	"""Resolve rules JSON using site config → remote → bundled fallback."""
	source_major = int(source_major)
	target_major = int(target_major)

	cache_key = _cache_key(source_major, target_major)
	cached = frappe.cache().get_value(cache_key)
	if cached:
		return cached

	rules: dict | None = None
	source = "bundled"

	site_url = frappe.conf.get("upgrade_lens_rules_url")
	if site_url:
		rules = _fetch_remote_rules(site_url)
		if rules:
			source = "site_config"

	if not rules:
		remote_url = _default_remote_url(source_major, target_major)
		rules = _fetch_remote_rules(remote_url)
		if rules:
			source = "remote"

	if not rules:
		rules = _load_bundled_rules(source_major, target_major)
		source = "bundled"

	if not rules:
		rules = {
			"source_major": source_major,
			"target_major": target_major,
			"infra_requirements": {},
			"deprecated_patterns": [],
			"unsupported_hooks": [],
			"new_native_fields": {},
			"heavy_tables": [],
			"bench_commands": {},
		}
		source = "empty_fallback"

	rules["_meta"] = {
		"source": source,
		"source_major": source_major,
		"target_major": target_major,
	}

	frappe.cache().set_value(cache_key, rules, expires_in_sec=6 * 3600)
	return rules


@frappe.whitelist()
def get_upgrade_rules(target_version: str) -> dict:
	_require_administrator()
	import frappe as frappe_module

	current_major = major_version(frappe_module.__version__) or 16
	target_major = major_version(target_version) or (current_major + 1)
	return get_rules(current_major, target_major)
