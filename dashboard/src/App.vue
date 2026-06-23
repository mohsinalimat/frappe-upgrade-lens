<script setup>
import { onMounted, ref } from "vue";
import { getDashboardSummary } from "./api.js";
import KpiHeader from "./components/KpiHeader.vue";
import CompatibilityGrid from "./components/CompatibilityGrid.vue";
import TabCodeScanner from "./components/TabCodeScanner.vue";
import TabStrategyPlanner from "./components/TabStrategyPlanner.vue";

const activeTab = ref("scanner");
const targetVersion = ref("");
const loading = ref(false);
const error = ref("");
const summary = ref(null);

async function loadSummary() {
	loading.value = true;
	error.value = "";
	try {
		summary.value = await getDashboardSummary(targetVersion.value || null);
		if (!targetVersion.value) {
			targetVersion.value = String(summary.value.target_major);
		}
	} catch (err) {
		error.value = err?.message || String(err);
	} finally {
		loading.value = false;
	}
}

onMounted(() => {
	loadSummary();
});
</script>

<template>
	<div class="upgrade-lens-dashboard">
		<div class="toolbar">
			<label>
				Target major version
				<input v-model="targetVersion" type="text" placeholder="e.g. 17" />
			</label>
			<button class="btn btn-primary btn-sm" :disabled="loading" @click="loadSummary">
				{{ loading ? "Scanning..." : "Run Scan" }}
			</button>
		</div>

		<div v-if="error" class="error-banner">{{ error }}</div>

		<template v-if="summary">
			<KpiHeader :summary="summary" />

			<h4 class="section-title">Compatibility</h4>
			<CompatibilityGrid :checks="summary.strategy?.infra_checks || []" />

			<div class="tabs">
				<button :class="{ active: activeTab === 'scanner' }" @click="activeTab = 'scanner'">
					Code &amp; Schema Scanner
				</button>
				<button :class="{ active: activeTab === 'strategy' }" @click="activeTab = 'strategy'">
					Strategy Planner
				</button>
			</div>

			<TabCodeScanner
				v-if="activeTab === 'scanner'"
				:conflicts="summary.conflicts"
				:apps="summary.apps"
			/>
			<TabStrategyPlanner v-else :strategy="summary.strategy" />
		</template>
	</div>
</template>

<style>
.upgrade-lens-dashboard {
	font-family: var(--font-stack, Inter, system-ui, sans-serif);
	padding: 8px 4px 24px;
}
.toolbar {
	display: flex;
	gap: 12px;
	align-items: end;
	margin-bottom: 16px;
}
.toolbar input {
	margin-left: 8px;
	padding: 6px 8px;
	border: 1px solid var(--border-color, #d1d8dd);
	border-radius: 4px;
}
.kpi-header {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
	gap: 12px;
	margin-bottom: 20px;
}
.kpi-card {
	background: var(--card-bg, #fff);
	border: 1px solid var(--border-color, #d1d8dd);
	border-radius: 8px;
	padding: 12px;
}
.kpi-label {
	font-size: 12px;
	color: var(--text-muted, #6c7680);
	text-transform: uppercase;
}
.kpi-value {
	font-size: 20px;
	font-weight: 600;
	margin-top: 4px;
}
.kpi-sub {
	font-size: 12px;
	color: var(--text-muted, #6c7680);
	margin-top: 4px;
}
.risk-badge {
	display: inline-block;
	padding: 4px 10px;
	border-radius: 999px;
	font-weight: 600;
	font-size: 13px;
}
.risk-low { background: #def7ec; color: #03543f; }
.risk-medium { background: #fef3c7; color: #92400e; }
.risk-high { background: #fde8e8; color: #9b1c1c; }
.compat-grid { border: 1px solid var(--border-color, #d1d8dd); border-radius: 8px; overflow: hidden; }
.compat-row {
	display: grid;
	grid-template-columns: 1fr 1.5fr 1.5fr 40px;
	gap: 8px;
	padding: 8px 12px;
	border-bottom: 1px solid var(--border-color, #edf2f7);
}
.compat-row:last-child { border-bottom: none; }
.pass { color: #057a55; font-weight: 700; }
.fail { color: #c81e1e; font-weight: 700; }
.tabs { display: flex; gap: 8px; margin: 20px 0 12px; }
.tabs button {
	border: 1px solid var(--border-color, #d1d8dd);
	background: #fff;
	padding: 8px 12px;
	border-radius: 6px;
	cursor: pointer;
}
.tabs button.active { background: #1e3a5f; color: #fff; border-color: #1e3a5f; }
.tab-panel section { margin-bottom: 20px; }
.path-card {
	border: 1px solid var(--border-color, #d1d8dd);
	border-radius: 8px;
	padding: 12px;
	margin-bottom: 12px;
}
.path-card.recommended { border-color: #1e3a5f; box-shadow: 0 0 0 1px #1e3a5f inset; }
.commands {
	background: #111827;
	color: #e5e7eb;
	padding: 10px;
	border-radius: 6px;
	overflow-x: auto;
	font-size: 12px;
}
.empty-state { color: var(--text-muted, #6c7680); font-style: italic; }
.error-banner {
	background: #fde8e8;
	color: #9b1c1c;
	padding: 10px 12px;
	border-radius: 6px;
	margin-bottom: 12px;
}
.section-title { margin: 16px 0 8px; }
</style>
