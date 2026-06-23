from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

from upgrade_lens.utils import version as version_utils


class TestVersionUtils(unittest.TestCase):
	def test_major_version(self):
		self.assertEqual(version_utils.major_version("16.22.0"), 16)
		self.assertIsNone(version_utils.major_version(None))

	def test_normalize_target_version(self):
		self.assertEqual(version_utils.normalize_target_version("17", "16.22.0"), "17.0.0")
		self.assertEqual(version_utils.normalize_target_version(None, "16.22.0"), "17.0.0")

	def test_compare_versions(self):
		self.assertEqual(version_utils.compare_versions("16.1.0", "16.2.0"), -1)
		self.assertEqual(version_utils.compare_versions("17.0.0", "16.9.9"), 1)


class TestRulesLoader(unittest.TestCase):
	@patch("upgrade_lens.api.rules.frappe")
	def test_load_bundled_rules(self, mock_frappe):
		mock_frappe.conf.get.return_value = None
		mock_frappe.cache.return_value.get_value.return_value = None
		mock_frappe.get_app_path.return_value = str(
			Path(__file__).resolve().parents[1] / "config" / "rules"
		)

		with patch("upgrade_lens.api.rules._load_bundled_rules") as bundled:
			bundled.return_value = {"source_major": 15, "target_major": 16, "infra_requirements": {}}
			from upgrade_lens.api.rules import get_rules

			result = get_rules(15, 16)
			self.assertEqual(result["source_major"], 15)


class TestStrategist(unittest.TestCase):
	def test_risk_level_bands(self):
		from upgrade_lens.api.strategist import _risk_level

		self.assertEqual(_risk_level(10), "Low")
		self.assertEqual(_risk_level(40), "Medium")
		self.assertEqual(_risk_level(80), "High")

	def test_build_strategy_paths(self):
		from upgrade_lens.api.strategist import build_strategy

		env = {
			"python_version": "3.12.0",
			"node_version": "v20.0.0",
			"db_type": "postgres",
			"db_version": "15.0",
			"site": "test.local",
		}
		db = {"size_gb": 1}
		apps = {"custom_apps": []}
		conflicts = {
			"client_scripts": [],
			"server_scripts": [],
			"schema_conflicts": [],
			"core_modifications": [],
		}
		rule_set = {
			"infra_requirements": {
				"python": ">=3.10,<3.14",
				"node": ">=18",
				"postgres": ">=13",
			},
			"bench_commands": {"in_place": ["bench --site {site} migrate"]},
		}

		result = build_strategy("17.0.0", rule_set, env, db, apps, conflicts)
		self.assertIn(result["risk_level"], ("Low", "Medium", "High"))
		recommended = [p for p in result["paths"] if p.get("recommended")]
		self.assertEqual(len(recommended), 1)
		self.assertEqual(result["recommended_path_id"], recommended[0]["id"])

	def test_infra_failure_recommends_clean_server(self):
		from upgrade_lens.api.strategist import build_strategy

		env = {
			"python_version": "3.14.5",
			"node_version": "v20.0.0",
			"db_type": "postgres",
			"db_version": "15.0",
			"site": "test.local",
		}
		rule_set = {
			"infra_requirements": {"python": ">=3.11,<3.14", "node": ">=18", "postgres": ">=13"},
			"bench_commands": {},
		}
		result = build_strategy(
			"17.0.0",
			rule_set,
			env,
			{"size_gb": 1, "heavy_tables": []},
			{"custom_apps": [], "total_apps": 2},
			{"client_scripts": [], "server_scripts": [], "schema_conflicts": [], "core_modifications": []},
		)
		self.assertEqual(result["recommended_path_id"], "C")

	def test_low_risk_recommends_in_place(self):
		from upgrade_lens.api.strategist import build_strategy

		env = {
			"python_version": "3.12.0",
			"node_version": "v20.0.0",
			"db_type": "postgres",
			"db_version": "15.0",
			"site": "test.local",
		}
		rule_set = {
			"infra_requirements": {"python": ">=3.10,<3.14", "node": ">=18", "postgres": ">=13"},
			"bench_commands": {},
		}
		result = build_strategy(
			"17.0.0",
			rule_set,
			env,
			{"size_gb": 0.5, "heavy_tables": []},
			{"custom_apps": [], "total_apps": 2},
			{"client_scripts": [], "server_scripts": [], "schema_conflicts": [], "core_modifications": []},
		)
		self.assertEqual(result["recommended_path_id"], "A")

	def test_fix_suggestion_for_python_too_new(self):
		from upgrade_lens.api.strategist import _fix_suggestion

		suggestion = _fix_suggestion("python", ">=3.11,<3.14", "3.14.5", False)
		self.assertIsNotNone(suggestion)
		self.assertIn("3.14.5", suggestion)
		self.assertIn("Downgrade", suggestion)


class TestGitAudit(unittest.TestCase):
	@patch("upgrade_lens.utils.git_audit._is_official_app", return_value=False)
	def test_skips_custom_app(self, _mock_official):
		from upgrade_lens.utils.git_audit import get_git_upstream_report

		report = get_git_upstream_report("my_custom_app")
		self.assertTrue(report["skipped"])
		self.assertEqual(report["reason"], "custom_app")

	@patch("upgrade_lens.utils.git_audit._get_registry", return_value={"frappe": {"official": True, "repo": "https://github.com/frappe/frappe"}})
	@patch("upgrade_lens.utils.git_audit._is_official_app", return_value=True)
	@patch("upgrade_lens.utils.git_audit.frappe")
	@patch("upgrade_lens.utils.git_audit._run_git")
	@patch("upgrade_lens.utils.git_audit._maybe_fetch_tags")
	@patch("upgrade_lens.utils.git_audit._resolve_upstream_ref", return_value="v16.22.0")
	def test_detects_uncommitted_working_tree_changes(
		self, _mock_ref, _mock_fetch, mock_git, mock_frappe, _mock_official, _mock_registry
	):
		from upgrade_lens.utils.git_audit import get_git_upstream_report

		mock_frappe.scrub.side_effect = lambda x: x
		mock_frappe.get_installed_apps.return_value = ["frappe"]
		mock_frappe.local.app_modules = {"frappe": True}
		mock_frappe.get_app_source_path.return_value = "/apps/frappe"
		mock_frappe.get_app_path.return_value = "/apps/frappe/frappe"
		mock_frappe.get_module.return_value = type("M", (), {"__version__": "16.22.0"})()

		def git_side_effect(app_path, *args):
			result = subprocess.CompletedProcess(args, 0, "", "")
			if args[:3] == ("diff", "--name-status", "v16.22.0"):
				result.stdout = "M\tfrappe/hooks.py\n"
			elif args[:3] == ("diff", "--name-status", "HEAD"):
				result.stdout = "M\tfrappe/hooks.py\n"
			return result

		import subprocess

		mock_git.side_effect = git_side_effect

		with patch("upgrade_lens.utils.git_audit._get_app_git_root") as mock_root:
			from pathlib import Path

			mock_root.return_value = Path("/apps/frappe")
			with patch("pathlib.Path.exists", return_value=True):
				report = get_git_upstream_report("frappe", "16.22.0")

		self.assertEqual(report["status"], "dirty")
		self.assertEqual(report["modified_count"], 1)
		self.assertTrue(report["has_uncommitted_changes"])


if __name__ == "__main__":
	unittest.main()
