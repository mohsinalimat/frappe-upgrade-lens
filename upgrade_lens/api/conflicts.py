"""Deprecated-pattern and schema conflict scanners."""

from __future__ import annotations

import re
from pathlib import Path

import frappe

from upgrade_lens.api.rules import get_rules
from upgrade_lens.utils.git_audit import get_git_upstream_report, summarize_hooks
from upgrade_lens.utils.version import major_version


def scan_conflicts(target_version: str) -> dict:
	current_major = major_version(frappe.__version__) or 16
	target_major = major_version(target_version) or (current_major + 1)
	rule_set = get_rules(current_major, target_major)

	return {
		"client_scripts": _scan_scripts("Client Script", rule_set),
		"server_scripts": _scan_scripts("Server Script", rule_set),
		"custom_apps_hooks": _scan_custom_app_hooks(rule_set),
		"schema_conflicts": _scan_schema_conflicts(rule_set),
		"core_modifications": _scan_core_modifications(),
	}


def _scan_scripts(doctype: str, rule_set: dict) -> list[dict]:
	patterns = rule_set.get("deprecated_patterns") or []
	if not patterns:
		return []

	compiled = [
		{
			**pattern,
			"compiled": re.compile(pattern["regex"]),
		}
		for pattern in patterns
		if pattern.get("regex")
	]

	hits: list[dict] = []
	scripts = frappe.get_all(
		doctype,
		fields=["name", "dt", "script", "enabled"],
		filters={"enabled": 1},
	)

	for script in scripts:
		content = script.script or ""
		for pattern in compiled:
			if pattern["compiled"].search(content):
				hits.append(
					{
						"doctype": doctype,
						"name": script.name,
						"reference_doctype": script.dt,
						"pattern_id": pattern.get("id"),
						"severity": pattern.get("severity", "medium"),
						"message": pattern.get("message"),
						"doc_url": pattern.get("doc_url"),
					}
				)

	return hits


def _scan_custom_app_hooks(rule_set: dict) -> list[dict]:
	unsupported = set(rule_set.get("unsupported_hooks") or [])
	if not unsupported:
		return []

	registry_path = Path(frappe.get_app_path("upgrade_lens", "config", "app_registry.json"))
	official_apps = set()
	try:
		import json

		registry = json.loads(registry_path.read_text(encoding="utf-8"))
		official_apps = {name for name, meta in registry.items() if meta.get("official")}
	except Exception:
		pass

	hits: list[dict] = []
	for app_name in frappe.get_installed_apps():
		if app_name in official_apps:
			continue

		summary = summarize_hooks(app_name)
		matched = sorted(set(summary.get("hook_keys") or []) & unsupported)
		if matched:
			hits.append(
				{
					"app": app_name,
					"unsupported_hooks": matched,
					"hooks_path": summary.get("hooks_path"),
				}
			)

	return hits


def _scan_schema_conflicts(rule_set: dict) -> list[dict]:
	new_fields = rule_set.get("new_native_fields") or {}
	if not new_fields:
		return []

	conflicts: list[dict] = []
	for doctype, native_fields in new_fields.items():
		for fieldname in native_fields:
			exists = frappe.db.exists(
				"Custom Field",
				{"dt": doctype, "fieldname": fieldname},
			)
			if exists:
				conflicts.append(
					{
						"doctype": doctype,
						"fieldname": fieldname,
						"custom_field": exists,
						"severity": "high",
						"message": f"Custom Field '{fieldname}' conflicts with incoming native field on {doctype}",
					}
				)

	return conflicts


def _scan_core_modifications() -> list[dict]:
	results: list[dict] = []
	registry_path = Path(frappe.get_app_path("upgrade_lens", "config", "app_registry.json"))
	try:
		import json

		registry = json.loads(registry_path.read_text(encoding="utf-8"))
	except Exception:
		return results

	for app_name, meta in registry.items():
		if not meta.get("official"):
			continue
		if app_name not in frappe.get_installed_apps():
			continue

		report = get_git_upstream_report(app_name)
		if report.get("modified_files"):
			results.append(report)

	return results


@frappe.whitelist()
def get_conflict_report(target_version: str) -> dict:
	if frappe.session.user != "Administrator":
		frappe.throw(frappe._("Only Administrator can run conflict scans."), frappe.PermissionError)
	return scan_conflicts(target_version)
