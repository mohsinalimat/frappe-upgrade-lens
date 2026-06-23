<script setup>
import { __ } from "../translate.js";
import SectionHeader from "./SectionHeader.vue";

defineProps({
	conflicts: { type: Object, default: () => ({}) },
	apps: { type: Object, default: () => ({}) },
});

const GIT_STATUS_LABELS = {
	clean: "Matches upstream — no local changes",
	dirty: "Modified files vs upstream tag",
	diverged: "Diverged from upstream (includes deletions)",
	no_git: "No git repository in app folder",
	skipped: "Custom app — upstream compare skipped",
	fetch_failed: "Could not fetch upstream tags",
	upstream_ref_not_found: "Upstream tag/branch not found",
	diff_failed: "Git diff could not be completed",
};

function count(items) {
	return items?.length || 0;
}

function gitStatusLabel(report) {
	if (!report) return "—";
	if (report.skipped) return __(GIT_STATUS_LABELS.skipped);
	const key = report.status;
	if (key && GIT_STATUS_LABELS[key]) return __(GIT_STATUS_LABELS[key]);
	return report.status || "—";
}
</script>

<template>
	<div class="widget-group">
		<p class="ul-tab-intro text-muted">
			{{
				__(
					"Scans your site for deprecated code, hook conflicts, schema overlaps, and changes to official app repositories. All checks are read-only."
				)
			}}
		</p>

		<div class="grid-col-2">
			<div class="widget border ul-scan-section">
				<SectionHeader
					:title="__('Client Scripts')"
					:description="
						__(
							'Browser-side JavaScript attached to DocTypes. Flags scripts using APIs or patterns removed or changed in the target version.'
						)
					"
					:count="count(conflicts.client_scripts)"
					:has-issues="count(conflicts.client_scripts) > 0"
				/>
				<ul v-if="conflicts.client_scripts?.length" class="ul-issue-list">
					<li
						v-for="hit in conflicts.client_scripts"
						:key="hit.name"
						:class="`issue-${hit.severity}`"
					>
						<strong>{{ hit.name }}</strong> · {{ hit.reference_doctype }}<br />
						<span class="text-muted">{{ hit.message }}</span>
					</li>
				</ul>
				<div v-else class="ul-empty">{{ __("No deprecated patterns detected") }}</div>
			</div>

			<div class="widget border ul-scan-section">
				<SectionHeader
					:title="__('Server Scripts')"
					:description="
						__(
							'Python scripts executed on the server for validations and automations. Detects deprecated frappe calls that may break after upgrade.'
						)
					"
					:count="count(conflicts.server_scripts)"
					:has-issues="count(conflicts.server_scripts) > 0"
				/>
				<ul v-if="conflicts.server_scripts?.length" class="ul-issue-list">
					<li
						v-for="hit in conflicts.server_scripts"
						:key="hit.name"
						:class="`issue-${hit.severity}`"
					>
						<strong>{{ hit.name }}</strong> · {{ hit.reference_doctype }}<br />
						<span class="text-muted">{{ hit.message }}</span>
					</li>
				</ul>
				<div v-else class="ul-empty">{{ __("No deprecated patterns detected") }}</div>
			</div>

			<div class="widget border ul-scan-section">
				<SectionHeader
					:title="__('Custom App Hooks')"
					:description="
						__(
							'Reviews hooks.py in non-official apps for registrations that the target version no longer supports or recommends replacing.'
						)
					"
					:count="count(conflicts.custom_apps_hooks)"
					:has-issues="count(conflicts.custom_apps_hooks) > 0"
				/>
				<ul v-if="conflicts.custom_apps_hooks?.length" class="ul-issue-list">
					<li v-for="hit in conflicts.custom_apps_hooks" :key="hit.app" class="issue-medium">
						<strong>{{ hit.app }}</strong>: {{ hit.unsupported_hooks.join(", ") }}
					</li>
				</ul>
				<div v-else class="ul-empty">{{ __("No unsupported hooks detected") }}</div>
			</div>

			<div class="widget border ul-scan-section">
				<SectionHeader
					:title="__('Schema Conflicts')"
					:description="
						__(
							'Compares Custom Field names against new native fields introduced in the target version. Overlapping names can cause migrate failures.'
						)
					"
					:count="count(conflicts.schema_conflicts)"
					:has-issues="count(conflicts.schema_conflicts) > 0"
				/>
				<ul v-if="conflicts.schema_conflicts?.length" class="ul-issue-list">
					<li v-for="hit in conflicts.schema_conflicts" :key="hit.custom_field" class="issue-high">
						{{ hit.message }}
					</li>
				</ul>
				<div v-else class="ul-empty">{{ __("No field name conflicts detected") }}</div>
			</div>

			<div class="widget border ul-scan-section full-width">
				<SectionHeader
					:title="__('Core App Modifications')"
					:description="
						__(
							'Compares official apps (frappe, erpnext, healthcare, etc.) against their upstream release tag. Local file changes increase upgrade risk and may be overwritten.'
						)
					"
					:count="count(conflicts.core_modifications)"
					:has-issues="count(conflicts.core_modifications) > 0"
				/>
				<ul v-if="conflicts.core_modifications?.length" class="ul-issue-list">
					<li
						v-for="report in conflicts.core_modifications"
						:key="report.app"
						:class="report.status === 'clean' ? '' : 'issue-high'"
					>
						<strong>{{ report.app }}</strong>
						<span
							class="indicator-pill no-indicator-dot filterable"
							:class="report.status === 'clean' ? 'green' : 'orange'"
						>
							{{ report.status }}
						</span>
						· {{ report.modified_count || 0 }} {{ __("files vs upstream") }}
						<span v-if="report.has_uncommitted_changes" class="indicator-pill no-indicator-dot red margin-left">
							{{ __("Uncommitted") }}
						</span>
						<ul v-if="report.modified_files?.length" class="margin-top text-small text-muted">
							<li v-for="file in report.modified_files.slice(0, 8)" :key="file.path">
								<code>{{ file.status }}</code> {{ file.path }}
							</li>
						</ul>
					</li>
				</ul>
				<div v-else class="ul-empty">{{ __("No modified core files detected") }}</div>
			</div>

			<div class="widget border ul-scan-section full-width">
				<SectionHeader
					:title="__('Installed Apps')"
					:description="
						__(
							'Lists every app on this bench with version, type, and git audit status. Custom apps are summarized only; official apps are compared to upstream.'
						)
					"
					:count="count(apps.apps)"
				/>
				<table class="table table-bordered">
					<thead>
						<tr>
							<th>{{ __("App") }}</th>
							<th>{{ __("Version") }}</th>
							<th>{{ __("Type") }}</th>
							<th>{{ __("Git Status") }}</th>
						</tr>
					</thead>
					<tbody>
						<tr v-for="app in apps.apps || []" :key="app.app">
							<td><strong>{{ app.app }}</strong></td>
							<td>{{ app.version || "—" }}</td>
							<td>
								<span
									class="indicator-pill no-indicator-dot filterable"
									:class="app.is_official ? 'blue' : 'purple'"
								>
									{{ app.is_official ? __("Official") : __("Custom") }}
								</span>
							</td>
							<td>
								<span class="text-muted text-small">{{ gitStatusLabel(app.git_report) }}</span>
							</td>
						</tr>
					</tbody>
				</table>
			</div>
		</div>
	</div>
</template>
