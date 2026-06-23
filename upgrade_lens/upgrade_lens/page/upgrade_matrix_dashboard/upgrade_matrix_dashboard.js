frappe.pages["upgrade-matrix-dashboard"].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Upgrade Matrix Dashboard"),
		single_column: true,
	});
};

frappe.pages["upgrade-matrix-dashboard"].on_page_show = function (wrapper) {
	load_upgrade_lens_dashboard(wrapper);
};

function load_upgrade_lens_dashboard(wrapper) {
	const $parent = $(wrapper).find(".layout-main-section");
	$parent.empty();

	frappe.require([
		"/assets/upgrade_lens/dist/style.css",
		"/assets/upgrade_lens/dist/upgrade_lens_dashboard.js",
	]).then(() => {
		if (frappe.ui.UpgradeLensDashboard) {
			frappe.upgrade_lens_dashboard = new frappe.ui.UpgradeLensDashboard({
				wrapper: $parent,
				page: wrapper.page,
			});
		}
	});
}
