"""Read-only git upstream comparison for official apps only."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import frappe

from upgrade_lens.utils.version import major_version

CACHE_KEY_PREFIX = "upgrade_lens:git_audit:"
MAX_DIFF_FILES = 500
GIT_TIMEOUT_SECONDS = 30
OFFICIAL_APP_NAMES: set[str] | None = None


def _get_registry() -> dict:
	registry_path = Path(frappe.get_app_path("upgrade_lens", "config", "app_registry.json"))
	return json.loads(registry_path.read_text(encoding="utf-8"))


def _is_official_app(app_name: str) -> bool:
	global OFFICIAL_APP_NAMES
	if OFFICIAL_APP_NAMES is None:
		registry = _get_registry()
		OFFICIAL_APP_NAMES = {name for name, meta in registry.items() if meta.get("official")}
	return app_name in OFFICIAL_APP_NAMES


def _git_enabled() -> bool:
	return bool(frappe.conf.get("upgrade_lens_git_fetch_enabled", True))


def _cache_hours() -> int:
	return int(frappe.conf.get("upgrade_lens_git_fetch_cache_hours", 24))


def _run_git(app_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
	return subprocess.run(
		["git", *args],
		cwd=app_path,
		capture_output=True,
		text=True,
		timeout=GIT_TIMEOUT_SECONDS,
		check=False,
	)


def _get_app_git_root(app_name: str) -> Path:
	"""Bench apps keep .git at the app source root (e.g. apps/frappe), not the package subfolder."""
	app_name = frappe.scrub(app_name)
	candidates = [
		Path(frappe.get_app_source_path(app_name)),
		Path(frappe.get_app_path(app_name)),
		Path(frappe.get_app_path(app_name)).parent,
	]
	for candidate in candidates:
		if (candidate / ".git").exists():
			return candidate.resolve()
	return Path(frappe.get_app_source_path(app_name)).resolve()


def _resolve_upstream_ref(app_name: str, app_version: str, registry_entry: dict) -> str | None:
	app_path = _get_app_git_root(app_name)
	if not (app_path / ".git").exists():
		return None

	tag_pattern = registry_entry.get("tag_pattern", "v{version}")
	tag_ref = tag_pattern.format(version=app_version)
	if _run_git(app_path, "rev-parse", "--verify", tag_ref).returncode == 0:
		return tag_ref

	major = major_version(app_version)
	if major is None:
		return None

	branch_pattern = registry_entry.get("version_branch_pattern", "version-{major}")
	branch_ref = branch_pattern.format(major=major)
	if _run_git(app_path, "rev-parse", "--verify", branch_ref).returncode == 0:
		return branch_ref

	remote_branch = f"origin/{branch_ref}"
	if _run_git(app_path, "rev-parse", "--verify", remote_branch).returncode == 0:
		return remote_branch

	return None


def _maybe_fetch_tags(app_name: str, app_path: Path) -> dict:
	if not _git_enabled():
		return {"fetched": False, "reason": "disabled"}

	cache_key = f"{CACHE_KEY_PREFIX}fetch:{app_name}"
	if frappe.cache().get_value(cache_key):
		return {"fetched": False, "reason": "cached"}

	registry_entry = _get_registry().get(app_name, {})
	repo_url = registry_entry.get("repo")
	if not repo_url:
		return {"fetched": False, "reason": "no_repo"}

	_run_git(app_path, "remote", "get-url", "origin")
	fetch = _run_git(app_path, "fetch", "--tags", "--quiet", "origin")
	frappe.cache().set_value(cache_key, True, expires_in_sec=_cache_hours() * 3600)

	if fetch.returncode != 0:
		return {"fetched": False, "reason": "fetch_failed", "stderr": (fetch.stderr or "").strip()}

	return {"fetched": True}


def get_git_upstream_report(app_name: str, app_version: str | None = None) -> dict:
	"""Compare an official app checkout against its upstream tag/branch."""
	app_name = frappe.scrub(app_name)

	if not _is_official_app(app_name):
		return {
			"app": app_name,
			"skipped": True,
			"reason": "custom_app",
			"status": "skipped",
		}

	if not frappe.local.app_modules.get(app_name) and app_name not in frappe.get_installed_apps():
		return {"app": app_name, "skipped": True, "reason": "not_installed", "status": "skipped"}

	registry_entry = _get_registry().get(app_name, {})
	app_path = _get_app_git_root(app_name)

	if not (app_path / ".git").exists():
		return {
			"app": app_name,
			"skipped": False,
			"status": "no_git",
			"modified_files": [],
		}

	if not app_version:
		app_version = _read_app_version(app_name)

	fetch_info = _maybe_fetch_tags(app_name, app_path)
	upstream_ref = _resolve_upstream_ref(app_name, app_version or "", registry_entry)

	if not upstream_ref:
		return {
			"app": app_name,
			"version": app_version,
			"skipped": False,
			"status": "upstream_ref_not_found",
			"fetch": fetch_info,
			"modified_files": [],
		}

	# Compare upstream tag/branch to the working tree (includes uncommitted local edits).
	diff = _run_git(app_path, "diff", "--name-status", upstream_ref)
	if diff.returncode != 0:
		return {
			"app": app_name,
			"version": app_version,
			"upstream_ref": upstream_ref,
			"status": "diff_failed",
			"fetch": fetch_info,
			"stderr": (diff.stderr or "").strip(),
			"modified_files": [],
		}

	modified_files = _parse_name_status(diff.stdout or "")

	# Track uncommitted changes separately for clearer reporting.
	uncommitted_diff = _run_git(app_path, "diff", "--name-status", "HEAD")
	uncommitted_files = _parse_name_status(uncommitted_diff.stdout or "") if uncommitted_diff.returncode == 0 else []

	truncated = len(modified_files) > MAX_DIFF_FILES
	if truncated:
		modified_files = modified_files[:MAX_DIFF_FILES]

	status = "clean" if not modified_files else "dirty"
	if modified_files and any(item["status"].startswith("D") for item in modified_files):
		status = "diverged"
	if uncommitted_files and status == "clean":
		status = "dirty"

	return {
		"app": app_name,
		"version": app_version,
		"upstream_ref": upstream_ref,
		"status": status,
		"fetch": fetch_info,
		"modified_files": modified_files,
		"modified_count": len(modified_files),
		"uncommitted_files": uncommitted_files,
		"uncommitted_count": len(uncommitted_files),
		"has_uncommitted_changes": bool(uncommitted_files),
		"truncated": truncated,
	}


def _read_app_version(app_name: str) -> str | None:
	try:
		module = frappe.get_module(app_name)
		return getattr(module, "__version__", None)
	except Exception:
		return None


def _parse_name_status(output: str) -> list[dict]:
	files: list[dict] = []
	for line in output.splitlines():
		line = line.strip()
		if not line:
			continue
		parts = line.split("\t", 1)
		if len(parts) != 2:
			continue
		status, path = parts
		files.append({"status": status, "path": path})
	return files


def summarize_hooks(app_name: str) -> dict:
	"""Lightweight hooks.py scan for custom apps (no upstream git diff)."""
	hooks_path = Path(frappe.get_app_path(app_name)) / app_name / "hooks.py"
	if not hooks_path.exists():
		hooks_path = Path(frappe.get_app_path(app_name)) / "hooks.py"

	if not hooks_path.exists():
		return {"hooks_path": None, "hook_keys": []}

	try:
		content = hooks_path.read_text(encoding="utf-8")
	except OSError:
		return {"hooks_path": str(hooks_path), "hook_keys": []}

	hook_keys = []
	for line in content.splitlines():
		stripped = line.strip()
		if not stripped or stripped.startswith("#"):
			continue
		if "=" in stripped and not stripped.startswith("def "):
			key = stripped.split("=", 1)[0].strip()
			if key.isidentifier():
				hook_keys.append(key)

	return {"hooks_path": str(hooks_path), "hook_keys": sorted(set(hook_keys))}
