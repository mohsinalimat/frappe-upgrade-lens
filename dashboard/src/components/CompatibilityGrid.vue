<script setup>
const props = defineProps({
	checks: { type: Array, default: () => [] },
});

function statusIcon(passed) {
	return passed ? "✓" : "✗";
}
</script>

<template>
	<div class="compat-grid">
		<div v-for="check in checks" :key="check.key" class="compat-row">
			<span class="compat-key">{{ check.key }}</span>
			<span class="compat-required">{{ check.required }}</span>
			<span class="compat-actual">{{ check.actual || "n/a" }}</span>
			<span :class="check.passed ? 'pass' : 'fail'">{{ statusIcon(check.passed) }}</span>
		</div>
		<div v-if="!checks.length" class="empty-state">No infrastructure requirements loaded.</div>
	</div>
</template>
