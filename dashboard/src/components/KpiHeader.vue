<script setup>
import RiskBadge from "./RiskBadge.vue";
import { __ } from "../translate.js";

defineProps({
	summary: { type: Object, required: true },
});
</script>

<template>
	<div class="widget-group">
		<div class="widget-group-head">
			<div>
				<div class="widget-group-title">{{ __("System Overview") }}</div>
				<p class="ul-section-desc text-muted">
					{{
						__(
							"Snapshot of your current stack, upgrade target, overall risk score, and database footprint before you migrate."
						)
					}}
				</p>
			</div>
		</div>
		<div class="grid-col-3">
			<div class="widget border number-widget-box">
				<div class="widget-head">
					<div class="widget-label">
						<div class="widget-title text-muted">{{ __("Current Version") }}</div>
					</div>
				</div>
				<div class="widget-body">
					<div class="widget-content">
						<div class="number">{{ summary.current_version }}</div>
					</div>
				</div>
			</div>

			<div class="widget border number-widget-box">
				<div class="widget-head">
					<div class="widget-label">
						<div class="widget-title text-muted">{{ __("Target Version") }}</div>
					</div>
				</div>
				<div class="widget-body">
					<div class="widget-content">
						<div class="number">{{ summary.target_version }}</div>
					</div>
				</div>
			</div>

			<div class="widget border number-widget-box">
				<div class="widget-head">
					<div class="widget-label">
						<div class="widget-title text-muted">{{ __("Risk Level") }}</div>
					</div>
				</div>
				<div class="widget-body">
					<div class="widget-content">
						<RiskBadge :level="summary.strategy?.risk_level" :score="summary.strategy?.risk_score" />
					</div>
				</div>
			</div>

			<div class="widget border number-widget-box">
				<div class="widget-head">
					<div class="widget-label">
						<div class="widget-title text-muted">{{ __("Database Size") }}</div>
					</div>
				</div>
				<div class="widget-body">
					<div class="widget-content">
						<div class="number">{{ summary.database?.size_gb }} GB</div>
						<div class="number-text text-muted">
							{{ __("Heaviest") }}: {{ summary.database?.heaviest_table?.doctype || "—" }}
							({{ summary.database?.heaviest_table?.row_count || 0 }} {{ __("rows") }})
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>
