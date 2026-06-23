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
		self.assertTrue(any(path["id"] == "A" for path in result["paths"]))


class TestGitAudit(unittest.TestCase):
	@patch("upgrade_lens.utils.git_audit._is_official_app", return_value=False)
	def test_skips_custom_app(self, _mock_official):
		from upgrade_lens.utils.git_audit import get_git_upstream_report

		report = get_git_upstream_report("react_platform")
		self.assertTrue(report["skipped"])
		self.assertEqual(report["reason"], "custom_app")


if __name__ == "__main__":
	unittest.main()
