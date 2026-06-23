"""Risk scoring and migration path recommendations."""

from __future__ import annotations

import re

import frappe

from upgrade_lens.utils.version import compare_versions, major_version


def _parse_spec_bounds(spec: str) -> tuple[str | None, str | None]:
	"""Return (min_version, max_exclusive) from a spec like '>=3.11,<3.14'."""
	min_ver = None
	max_ver = None
	for part in spec.split(","):
		part = part.strip()
		if part.startswith(">="):
			min_ver = part[2:].strip()
		elif part.startswith("<"):
			max_ver = part[1:].strip()
	return min_ver, max_ver


def _fix_suggestion(key: str, spec: str, actual: str | None, passed: bool) -> str | None:
	if passed:
		return None

	actual_clean = str(actual or "").lstrip("v") if actual else None
	min_ver, max_ver = _parse_spec_bounds(spec)
	label = key.replace("_", " ").title()

	if not actual_clean:
		hints = {
			"python": "Install a supported Python version and point bench to it: `bench setup env --python python3.12`.",
			"node": "Install Node.js 18+ (e.g. `nvm install 18` or `fnm install 18`) and rebuild assets with `bench build`.",
			"mariadb": "Install MariaDB 10.6+ or switch the site to a supported database server before upgrading.",
			"postgres": "Install PostgreSQL 13+ or migrate the site to a supported database server before upgrading.",
		}
		return hints.get(key, f"Install or configure {label} to satisfy: {spec}")

	if key == "python":
		if min_ver and compare_versions(actual_clean, min_ver) < 0:
			return (
				f"Python {actual_clean} is below the minimum ({min_ver}). "
				f"Install Python {min_ver}+ and recreate the bench env: "
				"`bench setup env --python python{min_ver.split('.')[0]}.{min_ver.split('.')[1]}`."
			)
		if max_ver and compare_versions(actual_clean, max_ver) >= 0:
			upper = max_ver.rstrip("=")
			recommended = upper
			if compare_versions(upper, "3.14") >= 0:
				recommended = "3.13.2"
			return (
				f"Python {actual_clean} is newer than supported ({spec}). "
				f"Downgrade to Python {recommended} (e.g. `pyenv install {recommended}`) and run "
				f"`bench setup env --python python{recommended}` on a staging bench before upgrading production."
			)

	if key == "node":
		if min_ver and compare_versions(actual_clean, min_ver) < 0:
			return (
				f"Node {actual_clean} is below the minimum ({min_ver}). "
				f"Upgrade with `nvm install {min_ver}` or `fnm install {min_ver}`, then run `bench build`."
			)

	if key in ("postgres", "mariadb"):
		if min_ver and compare_versions(actual_clean, min_ver) < 0:
			db_name = "PostgreSQL" if key == "postgres" else "MariaDB"
			return (
				f"{db_name} {actual_clean} is below the minimum ({min_ver}). "
				f"Upgrade the database server to {min_ver}+ on a staging environment, restore a backup, "
				f"and validate before upgrading production."
			)

	return f"Adjust {label} to satisfy {spec}. Current detected value: {actual_clean}."


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
		passed = _matches_spec(value, spec) if value else False
		checks.append(
			{
				"key": key,
				"required": spec,
				"actual": value,
				"passed": passed,
				"fix_suggestion": _fix_suggestion(key, spec, value, passed),
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


def _scan_context(
	env: dict,
	db: dict,
	apps: dict,
	conflicts: dict,
	infra_checks: list[dict],
	level: str,
	score: int,
) -> dict:
	core_dirty = [
		r for r in (conflicts.get("core_modifications") or []) if r.get("status") in ("dirty", "diverged")
	]
	script_hits = len(conflicts.get("client_scripts") or []) + len(conflicts.get("server_scripts") or [])
	schema_conflicts = len(conflicts.get("schema_conflicts") or [])
	hook_issues = len(conflicts.get("custom_apps_hooks") or [])
	custom_apps = apps.get("custom_apps") or []
	infra_compatible = all(row.get("passed", True) for row in infra_checks if row.get("actual"))
	infra_failures = [row for row in infra_checks if not row.get("passed")]
	heavy_rows = sum((row.get("row_count") or 0) for row in (db.get("heavy_tables") or []))
	db_size_gb = db.get("size_gb") or 0

	return {
		"risk_level": level,
		"risk_score": score,
		"infra_compatible": infra_compatible,
		"infra_failures": infra_failures,
		"core_dirty_count": len(core_dirty),
		"script_hits": script_hits,
		"schema_conflicts": schema_conflicts,
		"hook_issues": hook_issues,
		"custom_app_count": len(custom_apps),
		"custom_apps": custom_apps,
		"db_size_gb": db_size_gb,
		"heavy_log_rows": heavy_rows,
		"total_apps": apps.get("total_apps") or 0,
	}


def _all_path_definitions(commands: dict, site: str, target_major: int | None) -> dict[str, dict]:
	target_branch = f"version-{target_major}" if target_major else "version-<target>"
	return {
		"A": {
			"id": "A",
			"title": "Path A: In-Place Upgrade",
			"description": (
				"Upgrade this bench directly after a full backup. Suitable only when infrastructure "
				"is compatible, customization risk is low, and no core app files were modified."
			),
			"commands": _format_commands(commands.get("in_place"), site),
			"checklist": [
				"Announce a maintenance window to users",
				"Run `bench --site {site} backup --with-files`",
				"Update frappe/erpnext to the target branch on this bench",
				"Run `bench --site {site} migrate` and `bench build`",
				"Smoke-test login, sales cycle, and custom app routes",
				"Monitor Error Log for 24 hours after cutover",
			],
			"when_to_use": "Low risk, compatible stack, no core file drift, minimal scripts/hooks issues.",
		},
		"B": {
			"id": "B",
			"title": "Path B: Staging-First Clone",
			"description": (
				"Clone production to a staging bench, run the full upgrade there, and validate "
				"with UAT before touching production. The safest default for most real-world sites."
			),
			"commands": _format_commands(commands.get("staging"), site),
			"checklist": [
				"Provision staging server or bench matching target Python/Node/DB",
				"Backup production: `bench --site {site} backup --with-files`",
				"Restore backup on staging and install the same custom apps",
				"Run upgrade on staging and execute full UAT",
				"Re-run Upgrade Lens on staging and compare risk score",
				"Schedule production cutover only after staging sign-off",
			],
			"when_to_use": "Medium/high risk, custom apps, or any non-trivial customization.",
		},
		"C": {
			"id": "C",
			"title": "Path C: Clean Server Blueprint",
			"description": (
				"Provision a new server with a supported OS and stack, initialize a fresh bench on "
				"the target version, then restore data. Required when infrastructure checks fail."
			),
			"commands": _format_commands(commands.get("clean_server"), site),
			"checklist": [
				"Provision server with supported Python, Node, and database versions",
				f"Run `bench init <path> --frappe-branch {target_branch}`",
				"Install required apps at the target major version",
				"Restore latest site backup with files",
				"Run migrate, build, and full regression testing",
				"Switch DNS/load balancer only after validation",
			],
			"when_to_use": "Python, Node, or database version is outside target requirements.",
		},
		"D": {
			"id": "D",
			"title": "Path D: Staging + Customization Remediation",
			"description": (
				"Resolve deprecated scripts, hook conflicts, and schema overlaps on staging before "
				"attempting production upgrade. Best when custom apps drive most of the risk."
			),
			"commands": [
				"bench --site {site} backup --with-files",
				"bench new-site staging.local --install-app frappe",
				"# Install all custom apps on staging at target-compatible branches",
				"bench --site staging.local restore <backup-path>",
				"# Fix Client/Server Scripts and Custom Field conflicts reported by Upgrade Lens",
				"bench --site staging.local migrate",
				"bench build --app <custom-app>",
			],
			"checklist": [
				"Document every Client Script and Server Script flagged by the scan",
				"Refactor deprecated API usage in custom apps on a feature branch",
				"Rename or remove Custom Fields that conflict with incoming native fields",
				"Validate custom app hooks against target version docs",
				"Re-scan staging until risk score drops below Medium",
				"Then follow Path B cutover to production",
			],
			"when_to_use": "Multiple custom apps, script/hook hits, or schema conflicts detected.",
		},
		"E": {
			"id": "E",
			"title": "Path E: Database Housekeeping First",
			"description": (
				"Archive or purge heavy log tables and shrink the database before upgrade. "
				"Reduces migrate downtime and backup restore time on large sites."
			),
			"commands": [
				"bench --site {site} backup --with-files",
				"# Archive old Error Log / Activity Log rows (e.g. > 90 days)",
				"bench --site {site} console  # delete or archive stale log records",
				"bench --site {site} trim-database",
				"# Then proceed with staging clone (Path B)",
				"bench new-site staging.local",
				"bench --site staging.local restore <backup-path>",
			],
			"checklist": [
				"Review row counts in Error Log, Activity Log, Email Queue",
				"Export archives if retention policy requires keeping old logs",
				"Run `bench --site {site} trim-database` after cleanup",
				"Confirm reduced database size in Upgrade Lens",
				"Proceed with staging-first upgrade (Path B)",
			],
			"when_to_use": "Database over 10 GB or very large log tables.",
		},
		"F": {
			"id": "F",
			"title": "Path F: Core App Reconciliation",
			"description": (
				"Official app files differ from upstream. Reconcile or remove local core changes "
				"before upgrade so bench update does not silently overwrite custom patches."
			),
			"commands": [
				"# For each modified official app, review git diff vs upstream tag",
				"cd apps/frappe && git diff v<version>..HEAD --name-only",
				"# Move fixes into a custom app (override hooks) where possible",
				"bench --site {site} backup --with-files",
				"bench update --reset  # only after reconciling core changes",
				"bench --site {site} migrate",
			],
			"checklist": [
				"List every modified file in frappe/erpnext/official apps",
				"Port necessary changes into custom apps via hooks or overrides",
				"Reset or cherry-pick core repos back to clean upstream state",
				"Re-run Upgrade Lens until core modifications report is clean",
				"Continue with staging-first upgrade (Path B)",
			],
			"when_to_use": "Core frappe/erpnext files were modified vs upstream release.",
		},
	}


def _path_suitability(path_id: str, ctx: dict) -> tuple[int, str]:
	"""Return suitability score (0-100) and short rationale for a path."""
	if path_id == "C":
		if not ctx["infra_compatible"]:
			failures = ", ".join(row["key"] for row in ctx["infra_failures"]) or "infrastructure"
			return 95, f"Infrastructure checks failed ({failures})."
		return 15, "Infrastructure is compatible; a clean server is unnecessary."

	if not ctx["infra_compatible"]:
		return 5, "Blocked until infrastructure requirements are met (see Path C)."

	if path_id == "F":
		if ctx["core_dirty_count"]:
			return 90, f"{ctx['core_dirty_count']} official app(s) have local file drift from upstream."
		return 10, "No modified core app files detected."

	if path_id == "E":
		if ctx["db_size_gb"] > 10 or ctx["heavy_log_rows"] > 500_000:
			return 85, f"Large database ({ctx['db_size_gb']} GB) or heavy log tables detected."
		if ctx["db_size_gb"] > 5:
			return 55, "Moderate database size; housekeeping may shorten upgrade downtime."
		return 20, "Database size is small; housekeeping is optional."

	if path_id == "D":
		customization_score = (
			ctx["script_hits"] * 8
			+ ctx["hook_issues"] * 10
			+ ctx["schema_conflicts"] * 15
			+ min(ctx["custom_app_count"] * 12, 36)
		)
		if customization_score >= 30:
			return min(95, 60 + customization_score), (
				f"{ctx['custom_app_count']} custom app(s) and {ctx['script_hits'] + ctx['hook_issues']} "
				"script/hook issue(s) need remediation."
			)
		if ctx["custom_app_count"] >= 2:
			return 65, "Multiple custom apps increase upgrade coupling."
		return 25, "Few customization issues; dedicated remediation path is optional."

	if path_id == "B":
		score = 40
		reasons = []
		if ctx["risk_level"] == "High":
			score += 35
			reasons.append("high risk score")
		elif ctx["risk_level"] == "Medium":
			score += 25
			reasons.append("medium risk score")
		if ctx["custom_app_count"]:
			score += min(ctx["custom_app_count"] * 8, 24)
			reasons.append(f"{ctx['custom_app_count']} custom app(s)")
		if ctx["script_hits"] or ctx["schema_conflicts"]:
			score += 15
			reasons.append("scan conflicts present")
		if not reasons:
			reasons.append("safe default when not eligible for in-place upgrade")
		return min(score, 88), "; ".join(reasons).capitalize() + "."

	if path_id == "A":
		if ctx["risk_level"] != "Low":
			return 20, f"Risk level is {ctx['risk_level']}, not Low."
		if ctx["core_dirty_count"]:
			return 10, "Core app files were modified."
		if ctx["script_hits"] or ctx["schema_conflicts"] or ctx["hook_issues"]:
			return 15, "Script, hook, or schema conflicts must be resolved first."
		if ctx["custom_app_count"] > 1:
			return 35, "More than one custom app adds upgrade coupling."
		if ctx["db_size_gb"] > 10:
			return 30, "Large database increases in-place upgrade risk."
		return 92, "Low risk, compatible infrastructure, and minimal customization."

	return 0, "Not evaluated."


def _select_recommended_path(ctx: dict) -> str:
	ranked = sorted(
		((path_id, *_path_suitability(path_id, ctx)) for path_id in ("C", "F", "E", "D", "A", "B")),
		key=lambda row: row[1],
		reverse=True,
	)
	return ranked[0][0]


def _build_paths(commands: dict, site: str, ctx: dict, target_major: int | None) -> tuple[list[dict], str, str]:
	definitions = _all_path_definitions(commands, site, target_major)
	recommended_id = _select_recommended_path(ctx)
	recommended_score, recommended_reason = _path_suitability(recommended_id, ctx)

	paths: list[dict] = []
	for path_id, definition in definitions.items():
		score, rationale = _path_suitability(path_id, ctx)
		is_recommended = path_id == recommended_id
		paths.append(
			{
				**definition,
				"commands": [cmd.replace("{site}", site) for cmd in definition.get("commands") or []],
				"checklist": [item.replace("{site}", site) for item in definition.get("checklist") or []],
				"suitability_score": score,
				"suitability_rationale": rationale,
				"recommended": is_recommended,
				"applicable": score >= 25 or is_recommended,
			}
		)

	paths.sort(key=lambda p: (not p["recommended"], -p["suitability_score"], p["id"]))
	return paths, recommended_id, recommended_reason


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
	target_major = major_version(target_version)
	ctx = _scan_context(env, db, apps, conflicts, infra_checks, level, score)
	commands = rule_set.get("bench_commands") or {}
	paths, recommended_id, recommended_reason = _build_paths(commands, site, ctx, target_major)

	recommended_path = next((p for p in paths if p["id"] == recommended_id), None)

	return {
		"risk_score": score,
		"risk_level": level,
		"infra_checks": infra_checks,
		"infra_compatible": infra_compatible,
		"paths": paths,
		"recommended_path_id": recommended_id,
		"recommendation_summary": recommended_reason,
		"recommended_path_title": recommended_path.get("title") if recommended_path else None,
		"target_version": target_version,
		"target_major": target_major,
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
