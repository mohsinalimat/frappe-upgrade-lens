<script setup>
defineProps({
	title: { type: String, required: true },
	description: { type: String, default: "" },
	count: { type: Number, default: null },
	hasIssues: { type: Boolean, default: false },
});
</script>

<template>
	<div class="ul-section-header-block">
		<div class="section-head">
			<span>{{ title }}</span>
			<span
				v-if="count !== null"
				class="badge"
				:class="{ 'has-issues': hasIssues }"
			>
				{{ count }}
			</span>
		</div>
		<p v-if="description" class="ul-section-desc text-muted">{{ description }}</p>
	</div>
</template>
