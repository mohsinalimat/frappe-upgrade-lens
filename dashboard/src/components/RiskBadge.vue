<script setup>
const props = defineProps({
	level: { type: String, default: "Low" },
	score: { type: Number, default: 0 },
});

const colorClass = {
	Low: "risk-low",
	Medium: "risk-medium",
	High: "risk-high",
};
</script>

<template>
	<span class="risk-badge" :class="colorClass[level] || 'risk-low'">
		{{ level }} ({{ score }})
	</span>
</template>
