<script setup>
import { computed } from "vue";
import { __ } from "../translate.js";

const props = defineProps({
	checks: { type: Array, default: () => [] },
});

const passedCount = (checks) => checks.filter((c) => c.passed).length;
const failedChecks = computed(() => props.checks.filter((c) => !c.passed));
</script>

<template>
	<div class="form-section">
		<div class="section-body">
			<p class="ul-section-desc text-muted margin-bottom">
				{{
					__(
						"Validates Python, Node.js, and database versions against the target release requirements. Failed checks should be resolved on a staging bench first."
					)
				}}
			</p>
			<div v-if="checks.length" class="text-muted text-small margin-bottom">
				{{ passedCount(checks) }}/{{ checks.length }} {{ __("checks passed") }}
			</div>

			<div v-if="failedChecks.length" class="alert alert-warning ul-compat-alerts margin-bottom">
				<strong>{{ __("Action required") }}</strong>
				<ul class="ul-fix-list">
					<li v-for="check in failedChecks" :key="check.key">
						<span class="text-capitalize"><strong>{{ check.key }}</strong>:</span>
						{{ check.fix_suggestion }}
					</li>
				</ul>
			</div>

			<table class="table table-bordered">
				<thead>
					<tr>
						<th>{{ __("Component") }}</th>
						<th>{{ __("Required") }}</th>
						<th>{{ __("Detected") }}</th>
						<th style="width: 90px">{{ __("Status") }}</th>
						<th>{{ __("How to fix") }}</th>
					</tr>
				</thead>
				<tbody>
					<tr v-for="check in checks" :key="check.key" :class="{ 'ul-row-fail': !check.passed }">
						<td class="text-capitalize">{{ check.key }}</td>
						<td><code>{{ check.required }}</code></td>
						<td><code class="ul-detected">{{ check.actual || "n/a" }}</code></td>
						<td>
							<span
								class="indicator-pill no-indicator-dot"
								:class="check.passed ? 'green' : 'red'"
							>
								{{ check.passed ? __("Pass") : __("Fail") }}
							</span>
						</td>
						<td class="ul-fix-cell">
							<span v-if="check.passed" class="text-muted">—</span>
							<span v-else class="text-small">{{ check.fix_suggestion }}</span>
						</td>
					</tr>
					<tr v-if="!checks.length">
						<td colspan="5" class="text-muted text-center">
							{{ __("No infrastructure requirements loaded.") }}
						</td>
					</tr>
				</tbody>
			</table>
		</div>
	</div>
</template>
