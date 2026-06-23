<script setup>
import { computed } from "vue";
import { __ } from "../translate.js";

const props = defineProps({
	strategy: { type: Object, default: () => ({}) },
});

const recommendedPath = computed(() =>
	(props.strategy.paths || []).find((path) => path.recommended),
);
const alternativePaths = computed(() =>
	(props.strategy.paths || []).filter((path) => !path.recommended && path.applicable),
);
const lowFitPaths = computed(() =>
	(props.strategy.paths || []).filter((path) => !path.recommended && !path.applicable),
);

function copyCommands(commands) {
	const text = (commands || []).join("\n");
	frappe.utils.copy_to_clipboard(text);
	frappe.show_alert({ message: __("Commands copied"), indicator: "green" });
}
</script>

<template>
	<div class="widget-group">
		<p class="ul-tab-intro text-muted">
			{{
				__(
					"Six migration scenarios are evaluated from your scan. Only the best-fit path is recommended; others are shown when relevant with suitability notes."
				)
			}}
		</p>

		<div v-if="recommendedPath" class="alert alert-success ul-recommendation-banner">
			<strong>{{ __("Recommended") }}: {{ recommendedPath.title }}</strong>
			<p class="margin-0 text-small">
				{{ strategy.recommendation_summary || recommendedPath.suitability_rationale }}
			</p>
		</div>

		<div v-if="recommendedPath" class="ul-path-card recommended">
			<h4>
				{{ recommendedPath.title }}
				<span class="indicator-pill no-indicator-dot green margin-left">
					{{ __("Best fit") }} · {{ recommendedPath.suitability_score }}%
				</span>
			</h4>
			<p>{{ recommendedPath.description }}</p>
			<p class="text-muted text-small">
				<strong>{{ __("When to use") }}:</strong> {{ recommendedPath.when_to_use }}
			</p>
			<ul class="checklist">
				<li v-for="item in recommendedPath.checklist || []" :key="item">{{ item }}</li>
			</ul>
			<pre class="ul-commands">{{ (recommendedPath.commands || []).join("\n") }}</pre>
			<button class="btn btn-primary btn-sm" @click="copyCommands(recommendedPath.commands)">
				{{ __("Copy Commands") }}
			</button>
		</div>

		<template v-if="alternativePaths.length">
			<div class="ul-section-label">{{ __("Alternative scenarios") }}</div>
			<p class="ul-tab-hint text-muted text-small">
				{{ __("Viable if your constraints change, but not the best match for this scan.") }}
			</p>
			<div
				v-for="path in alternativePaths"
				:key="path.id"
				class="ul-path-card ul-path-alt"
			>
				<h4>
					{{ path.title }}
					<span class="indicator-pill no-indicator-dot blue margin-left">
						{{ __("Suitability") }} {{ path.suitability_score }}%
					</span>
				</h4>
				<p>{{ path.description }}</p>
				<p class="text-muted text-small">
					<strong>{{ __("Why not primary") }}:</strong> {{ path.suitability_rationale }}
				</p>
				<p class="text-muted text-small">
					<strong>{{ __("When to use") }}:</strong> {{ path.when_to_use }}
				</p>
				<details class="ul-path-details">
					<summary class="text-small">{{ __("Show checklist and commands") }}</summary>
					<ul class="checklist">
						<li v-for="item in path.checklist || []" :key="item">{{ item }}</li>
					</ul>
					<pre class="ul-commands">{{ (path.commands || []).join("\n") }}</pre>
					<button class="btn btn-default btn-sm" @click="copyCommands(path.commands)">
						{{ __("Copy Commands") }}
					</button>
				</details>
			</div>
		</template>

		<template v-if="lowFitPaths.length">
			<div class="ul-section-label">{{ __("Not recommended for this site") }}</div>
			<div v-for="path in lowFitPaths" :key="path.id" class="ul-path-card ul-path-muted">
				<h4 class="text-muted">{{ path.title }}</h4>
				<p class="text-muted text-small">{{ path.suitability_rationale }}</p>
			</div>
		</template>

		<div v-if="!recommendedPath && !props.strategy.paths?.length" class="ul-empty">
			{{ __("No migration paths available for this scan.") }}
		</div>
	</div>
</template>
