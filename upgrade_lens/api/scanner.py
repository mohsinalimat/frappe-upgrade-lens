"""Read-only system and app scanners for the upgrade dashboard."""

from __future__ import annotations

import importlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import frappe

from upgrade_lens.api import conflicts, rules, strategist
from upgrade_lens.utils import db_metrics
from upgrade_lens.utils.git_audit import get_git_upstream_report, summarize_hooks
from upgrade_lens.utils.version import major_version, normalize_target_version


def _require_administrator() -> None:
	if frappe.session.user != "Administrator":
		frappe.throw(
			frappe._("Only Administrator can run upgrade assessments."),
			frappe.PermissionError,
		)


def _read_apps_txt() -> list[str]:
	apps_path = Path(frappe.get_site_path("..", "apps.txt"))
	if not apps_path.exists():
		return list(frappe.get_installed_apps())
	return [line.strip() for line in apps_path.read_text().splitlines() if line.strip()]


def _read_app_version(app_name: str) -> str | None:
	try:
		module = importlib.import_module(app_name)
		return getattr(module, "__version__", None)
	except Exception:
		return None


def _read_pyproject_repo(app_name: str) -> str | None:
	app_path = Path(frappe.get_app_path(app_name))
	pyproject = app_path.parent / "pyproject.toml"
	if not pyproject.exists():
		pyproject = app_path / "pyproject.toml"
	if not pyproject.exists():
		return None

	try:
		content = pyproject.read_text(encoding="utf-8")
	except OSError:
		return None

	for pattern in (
		r'(?im)^\s*Homepage\s*=\s*"([^"]+)"',
		r'(?im)^\s*repository\s*=\s*"([^"]+)"',
	):
		match = re.search(pattern, content)
		if match:
			return match.group(1)
	return None


def _load_app_registry() -> dict:
	registry_path = Path(frappe.get_app_path("upgrade_lens", "config", "app_registry.json"))
	return json.loads(registry_path.read_text(encoding="utf-8"))


def _get_node_version() -> str | None:
	try:
		result = subprocess.run(
			["node", "--version"],
			capture_output=True,
			text=True,
			timeout=10,
			check=False,
		)
		if result.returncode == 0:
			return result.stdout.strip()
	except Exception:
		return None
	return None


def _get_python_version() -> str:
	return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


@frappe.whitelist()
def get_environment_specs() -> dict:
	_require_administrator()
	return {
		"python_version": _get_python_version(),
		"node_version": _get_node_version(),
		"db_type": frappe.conf.get("db_type") or "mariadb",
		"db_version": db_metrics.get_db_server_version(),
		"frappe_version": frappe.__version__,
		"site": frappe.local.site,
		"bench_path": os.path.abspath(frappe.get_site_path("..", "..")),
	}


@frappe.whitelist()
def get_database_metrics() -> dict:
	_require_administrator()
	rule_set = rules.get_rules(
		major_version(frappe.__version__) or 16,
		(major_version(frappe.__version__) or 16) + 1,
	)
	return db_metrics.get_database_metrics(rule_set.get("heavy_tables"))


@frappe.whitelist()
def get_installed_apps_audit() -> dict:
	_require_administrator()
	registry = _load_app_registry()
	apps_report: list[dict] = []

	for app_name in _read_apps_txt():
		if app_name not in frappe.get_installed_apps():
			continue

		version = _read_app_version(app_name)
		registry_entry = registry.get(app_name, {})
		is_official = bool(registry_entry.get("official"))
		repo = registry_entry.get("repo") or _read_pyproject_repo(app_name)

		entry = {
			"app": app_name,
			"version": version,
			"major_version": major_version(version),
			"is_official": is_official,
			"repo": repo,
			"in_registry": app_name in registry,
		}

		if is_official:
			entry["git_report"] = get_git_upstream_report(app_name, version)
		else:
			entry["git_report"] = {"skipped": True, "reason": "custom_app", "status": "skipped"}
			entry["hooks_summary"] = summarize_hooks(app_name)

		apps_report.append(entry)

	return {
		"apps": apps_report,
		"total_apps": len(apps_report),
		"custom_apps": [row["app"] for row in apps_report if not row["is_official"]],
		"official_apps": [row["app"] for row in apps_report if row["is_official"]],
	}


@frappe.whitelist()
def get_git_upstream_report_api(app_name: str) -> dict:
	_require_administrator()
	return get_git_upstream_report(app_name)


@frappe.whitelist()
def get_dashboard_summary(target_version: str | None = None) -> dict:
	_require_administrator()
	target_version = normalize_target_version(target_version, frappe.__version__)
	current_major = major_version(frappe.__version__) or 16
	target_major = major_version(target_version) or (current_major + 1)

	rule_set = rules.get_rules(current_major, target_major)
	env = get_environment_specs()
	db = db_metrics.get_database_metrics(rule_set.get("heavy_tables"))
	apps = get_installed_apps_audit()
	conflict_report = conflicts.scan_conflicts(target_version)
	strategy = strategist.build_strategy(target_version, rule_set, env, db, apps, conflict_report)

	return {
		"current_version": frappe.__version__,
		"target_version": target_version,
		"current_major": current_major,
		"target_major": target_major,
		"environment": env,
		"database": db,
		"apps": apps,
		"conflicts": conflict_report,
		"strategy": strategy,
		"rules_meta": rule_set.get("_meta", {}),
	}


@frappe.whitelist()
def run_full_scan(target_version: str | None = None) -> dict:
	_require_administrator()
	return get_dashboard_summary(target_version)
