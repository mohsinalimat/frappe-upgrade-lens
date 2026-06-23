<script setup>
import RiskBadge from "./RiskBadge.vue";

const props = defineProps({
	summary: { type: Object, required: true },
});
</script>

<template>
	<div class="kpi-header">
		<div class="kpi-card">
			<div class="kpi-label">Current Version</div>
			<div class="kpi-value">{{ summary.current_version }}</div>
		</div>
		<div class="kpi-card">
			<div class="kpi-label">Target Version</div>
			<div class="kpi-value">{{ summary.target_version }}</div>
		</div>
		<div class="kpi-card">
			<div class="kpi-label">Risk Level</div>
			<RiskBadge :level="summary.strategy?.risk_level" :score="summary.strategy?.risk_score" />
		</div>
		<div class="kpi-card">
			<div class="kpi-label">Database Size</div>
			<div class="kpi-value">{{ summary.database?.size_gb }} GB</div>
			<div class="kpi-sub">
				Heaviest: {{ summary.database?.heaviest_table?.doctype || "—" }}
				({{ summary.database?.heaviest_table?.row_count || 0 }} rows)
			</div>
		</div>
	</div>
</template>
