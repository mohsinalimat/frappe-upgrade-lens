"""Risk scoring and migration path recommendations."""

from __future__ import annotations

import re

import frappe

from upgrade_lens.utils.version import compare_versions, major_version


def _infra_check(env: dict, rule_set: dict) -> list[dict]:
	requirements = rule_set.get("infra_requirements") or {}
	checks: list[dict] = []

	spec_map = {
		"python": env.get("python_version"),
		"node": (env.get("node_version") or "").lstrip("v"),
		"mariadb": env.get("db_version") if env.get("db_type") == "mariadb" else None,
		"postgres": env.get("db_version") if env.get("db_type") == "postgres" else None,
	}

	for key, spec in requirements.items():
		value = spec_map.get(key)
		if value is None and key in ("mariadb", "postgres"):
			continue
		checks.append(
			{
				"key": key,
				"required": spec,
				"actual": value,
				"passed": _matches_spec(value, spec) if value else False,
			}
		)

	return checks


def _matches_spec(value: str | None, spec: str) -> bool:
	if not value or not spec:
		return False

	value = str(value).lstrip("v")
	for part in spec.split(","):
		part = part.strip()
		if part.startswith(">="):
			if compare_versions(value, part[2:].strip()) < 0:
				return False
		elif part.startswith("<"):
			if compare_versions(value, part[1:].strip()) >= 0:
				return False
	return True


def _risk_level(score: int) -> str:
	if score <= 25:
		return "Low"
	if score <= 60:
		return "Medium"
	return "High"


def _risk_score(
	env: dict,
	db: dict,
	apps: dict,
	conflicts: dict,
	infra_checks: list[dict],
) -> int:
	score = 0

	for report in conflicts.get("core_modifications") or []:
		if report.get("status") in ("dirty", "diverged"):
			score += 30

	script_hits = len(conflicts.get("client_scripts") or []) + len(
		conflicts.get("server_scripts") or []
	)
	score += min(script_hits * 5, 25)

	score += len(conflicts.get("schema_conflicts") or []) * 15
	score += min(len(apps.get("custom_apps") or []) * 3, 15)

	if any(not row.get("passed") for row in infra_checks):
		score += 20

	if (db.get("size_gb") or 0) > 10:
		score += 10

	return min(score, 100)


def _format_commands(command_list: list[str] | None, site: str) -> list[str]:
	if not command_list:
		return []
	return [cmd.replace("{site}", site) for cmd in command_list]


def build_strategy(
	target_version: str,
	rule_set: dict,
	env: dict,
	db: dict,
	apps: dict,
	conflicts: dict,
) -> dict:
	site = env.get("site") or frappe.local.site
	infra_checks = _infra_check(env, rule_set)
	infra_compatible = all(row.get("passed", True) for row in infra_checks if row.get("actual"))
	score = _risk_score(env, db, apps, conflicts, infra_checks)
	level = _risk_level(score)

	commands = rule_set.get("bench_commands") or {}
	paths = []

	if infra_compatible and level == "Low":
		paths.append(
			{
				"id": "A",
				"title": "Path A: In-Place Upgrade",
				"recommended": True,
				"description": "Low customization risk and compatible infrastructure. Upgrade on this bench after a full backup.",
				"commands": _format_commands(commands.get("in_place"), site),
				"checklist": [
					"Take a full site backup with files",
					"Notify users of maintenance window",
					"Run commands sequentially on a terminal",
					"Smoke-test critical workflows after migrate",
				],
			}
		)

	if level in ("Medium", "High") or not infra_compatible:
		paths.append(
			{
				"id": "B",
				"title": "Path B: Staging-First Cloning",
				"recommended": level != "Low",
				"description": "Clone to a staging bench, run the upgrade there, and validate before touching production.",
				"commands": _format_commands(commands.get("staging"), site),
				"checklist": [
					"Provision staging bench matching target stack",
					"Restore latest production backup",
					"Run full scan on staging after upgrade",
					"Execute UAT sign-off before production cutover",
				],
			}
		)

	if not infra_compatible:
		paths.append(
			{
				"id": "C",
				"title": "Path C: Clean Server Blueprint",
				"recommended": True,
				"description": "Infrastructure does not meet target requirements. Provision a clean server on a supported stack.",
				"commands": _format_commands(commands.get("clean_server"), site),
				"checklist": [
					"Provision OS with supported Python, Node, and database versions",
					"Initialize a fresh bench on the target major version",
					"Restore data backup only after apps are installed",
					"Re-run Upgrade Lens on the new instance",
				],
			}
		)

	return {
		"risk_score": score,
		"risk_level": level,
		"infra_checks": infra_checks,
		"infra_compatible": infra_compatible,
		"paths": paths,
		"target_version": target_version,
		"target_major": major_version(target_version),
	}


@frappe.whitelist()
def get_migration_strategy(target_version: str) -> dict:
	if frappe.session.user != "Administrator":
		frappe.throw(frappe._("Only Administrator can view migration strategy."), frappe.PermissionError)

	from upgrade_lens.api import conflicts, rules, scanner
	from upgrade_lens.utils import db_metrics

	current_major = major_version(frappe.__version__) or 16
	target_major = major_version(target_version) or (current_major + 1)
	rule_set = rules.get_rules(current_major, target_major)
	env = scanner.get_environment_specs()
	db = db_metrics.get_database_metrics(rule_set.get("heavy_tables"))
	apps = scanner.get_installed_apps_audit()
	conflict_report = conflicts.scan_conflicts(target_version)

	return build_strategy(target_version, rule_set, env, db, apps, conflict_report)
