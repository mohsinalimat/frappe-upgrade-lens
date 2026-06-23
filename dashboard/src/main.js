import { createApp } from "vue";
import App from "./App.vue";

class UpgradeLensDashboard {
	constructor({ wrapper, page }) {
		this.$wrapper = $(wrapper);
		this.page = page;
		this.mount();
	}

	mount() {
		this.page.set_title(__("Upgrade Matrix Dashboard"));
		this.app = createApp(App);
		this.vm = this.app.mount(this.$wrapper[0]);
	}
}

if (typeof frappe !== "undefined") {
	frappe.provide("frappe.ui");
	frappe.ui.UpgradeLensDashboard = UpgradeLensDashboard;
}

export default UpgradeLensDashboard;
