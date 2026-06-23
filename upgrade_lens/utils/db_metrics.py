"""Database size and heavy-table metrics (MariaDB + PostgreSQL)."""

from __future__ import annotations

import frappe


DEFAULT_HEAVY_TABLES = [
	"Error Log",
	"Activity Log",
	"Email Queue",
	"Version",
	"Communication",
]


def get_database_size_bytes() -> int:
	db_type = frappe.conf.get("db_type") or "mariadb"
	if db_type == "postgres":
		result = frappe.db.sql("SELECT pg_database_size(current_database())", as_list=True)
		return int(result[0][0]) if result else 0

	result = frappe.db.sql(
		"""
		SELECT SUM(data_length + index_length)
		FROM information_schema.tables
		WHERE table_schema = %s
		""",
		(frappe.conf.db_name,),
		as_list=True,
	)
	return int(result[0][0] or 0) if result else 0


def get_db_server_version() -> str | None:
	try:
		if (frappe.conf.get("db_type") or "mariadb") == "postgres":
			result = frappe.db.sql("SELECT version()", as_list=True)
		else:
			result = frappe.db.sql("SELECT VERSION()", as_list=True)
		return str(result[0][0]) if result else None
	except Exception:
		return None


def get_heavy_table_counts(table_names: list[str] | None = None) -> list[dict]:
	tables = table_names or DEFAULT_HEAVY_TABLES
	rows: list[dict] = []

	for doctype in tables:
		if not frappe.db.table_exists(f"tab{doctype}"):
			rows.append({"doctype": doctype, "row_count": 0, "exists": False})
			continue

		count = frappe.db.count(doctype)
		rows.append({"doctype": doctype, "row_count": count, "exists": True})

	rows.sort(key=lambda row: row["row_count"], reverse=True)
	return rows


def get_database_metrics(table_names: list[str] | None = None) -> dict:
	size_bytes = get_database_size_bytes()
	heavy_tables = get_heavy_table_counts(table_names)

	return {
		"db_type": frappe.conf.get("db_type") or "mariadb",
		"db_version": get_db_server_version(),
		"size_bytes": size_bytes,
		"size_mb": round(size_bytes / (1024 * 1024), 2),
		"size_gb": round(size_bytes / (1024 * 1024 * 1024), 2),
		"heavy_tables": heavy_tables,
		"heaviest_table": heavy_tables[0] if heavy_tables else None,
	}
