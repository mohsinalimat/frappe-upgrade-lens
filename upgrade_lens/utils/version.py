"""Version parsing helpers for upgrade assessments."""

from __future__ import annotations

import re


def major_version(version: str | None) -> int | None:
	if not version:
		return None
	match = re.match(r"^(\d+)", str(version).strip())
	return int(match.group(1)) if match else None


def normalize_target_version(target_version: str | None, current_version: str) -> str:
	"""Return a dotted version string for the selected target major."""
	if not target_version:
		current_major = major_version(current_version) or 16
		return f"{current_major + 1}.0.0"

	target_version = str(target_version).strip()
	if re.match(r"^\d+$", target_version):
		return f"{target_version}.0.0"
	if re.match(r"^\d+\.\d+$", target_version):
		return f"{target_version}.0"
	return target_version


def version_tuple(version: str | None) -> tuple[int, ...]:
	if not version:
		return (0,)
	parts = re.findall(r"\d+", str(version))
	return tuple(int(part) for part in parts) or (0,)


def compare_versions(left: str | None, right: str | None) -> int:
	"""Return -1 if left < right, 0 if equal, 1 if left > right."""
	left_parts = version_tuple(left)
	right_parts = version_tuple(right)
	max_len = max(len(left_parts), len(right_parts))
	for index in range(max_len):
		lv = left_parts[index] if index < len(left_parts) else 0
		rv = right_parts[index] if index < len(right_parts) else 0
		if lv < rv:
			return -1
		if lv > rv:
			return 1
	return 0
