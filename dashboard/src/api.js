function frappeCall(method, args = {}) {
	return new Promise((resolve, reject) => {
		frappe.call({
			method,
			args,
			callback: (response) => resolve(response.message),
			error: (error) => reject(error),
		});
	});
}

export function getDashboardSummary(targetVersion) {
	return frappeCall("upgrade_lens.api.scanner.get_dashboard_summary", {
		target_version: targetVersion,
	});
}

export function runFullScan(targetVersion) {
	return frappeCall("upgrade_lens.api.scanner.run_full_scan", {
		target_version: targetVersion,
	});
}
