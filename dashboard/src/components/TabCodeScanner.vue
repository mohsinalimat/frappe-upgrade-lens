<script setup>
const props = defineProps({
	conflicts: { type: Object, default: () => ({}) },
	apps: { type: Object, default: () => ({}) },
});
</script>

<template>
	<div class="tab-panel">
		<section>
			<h4>Client Scripts</h4>
			<ul v-if="conflicts.client_scripts?.length">
				<li v-for="hit in conflicts.client_scripts" :key="hit.name">
					<strong>{{ hit.name }}</strong> on {{ hit.reference_doctype }} —
					{{ hit.message }} ({{ hit.severity }})
				</li>
			</ul>
			<p v-else class="empty-state">No deprecated patterns in Client Scripts.</p>
		</section>

		<section>
			<h4>Server Scripts</h4>
			<ul v-if="conflicts.server_scripts?.length">
				<li v-for="hit in conflicts.server_scripts" :key="hit.name">
					<strong>{{ hit.name }}</strong> on {{ hit.reference_doctype }} —
					{{ hit.message }} ({{ hit.severity }})
				</li>
			</ul>
			<p v-else class="empty-state">No deprecated patterns in Server Scripts.</p>
		</section>

		<section>
			<h4>Custom App Hooks</h4>
			<ul v-if="conflicts.custom_apps_hooks?.length">
				<li v-for="hit in conflicts.custom_apps_hooks" :key="hit.app">
					<strong>{{ hit.app }}</strong>: {{ hit.unsupported_hooks.join(", ") }}
				</li>
			</ul>
			<p v-else class="empty-state">No unsupported hooks in custom apps.</p>
		</section>

		<section>
			<h4>Schema Conflicts</h4>
			<ul v-if="conflicts.schema_conflicts?.length">
				<li v-for="hit in conflicts.schema_conflicts" :key="hit.custom_field">
					{{ hit.message }}
				</li>
			</ul>
			<p v-else class="empty-state">No custom field name conflicts detected.</p>
		</section>

		<section>
			<h4>Core App Modifications</h4>
			<div v-for="report in conflicts.core_modifications" :key="report.app" class="core-report">
				<strong>{{ report.app }}</strong> — {{ report.status }}
				({{ report.modified_count || 0 }} files)
				<ul v-if="report.modified_files?.length">
					<li v-for="file in report.modified_files.slice(0, 10)" :key="file.path">
						{{ file.status }} {{ file.path }}
					</li>
				</ul>
			</div>
			<p v-if="!conflicts.core_modifications?.length" class="empty-state">
				No modified core app files detected.
			</p>
		</section>

		<section>
			<h4>Installed Apps</h4>
			<ul>
				<li v-for="app in apps.apps || []" :key="app.app">
					<strong>{{ app.app }}</strong> {{ app.version }}
					<span v-if="app.is_official">(official)</span>
					<span v-else>(custom)</span>
				</li>
			</ul>
		</section>
	</div>
</template>
