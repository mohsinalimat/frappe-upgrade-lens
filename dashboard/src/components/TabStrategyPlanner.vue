<script setup>
const props = defineProps({
	strategy: { type: Object, default: () => ({}) },
});

function copyCommands(commands) {
	const text = (commands || []).join("\n");
	frappe.utils.copy_to_clipboard(text);
	frappe.show_alert({ message: __("Commands copied"), indicator: "green" });
}
</script>

<template>
	<div class="tab-panel">
		<div v-for="path in strategy.paths || []" :key="path.id" class="path-card" :class="{ recommended: path.recommended }">
			<h4>{{ path.title }}</h4>
			<p>{{ path.description }}</p>
			<ul class="checklist">
				<li v-for="item in path.checklist || []" :key="item">{{ item }}</li>
			</ul>
			<pre class="commands">{{ (path.commands || []).join("\n") }}</pre>
			<button class="btn btn-sm btn-default" @click="copyCommands(path.commands)">Copy Commands</button>
		</div>
		<p v-if="!strategy.paths?.length" class="empty-state">No migration paths available for this scan.</p>
	</div>
</template>
