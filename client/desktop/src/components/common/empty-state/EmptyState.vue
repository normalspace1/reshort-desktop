<script setup lang="ts">
import type { Component } from 'vue'

interface Props {
	icon?: Component
	title: string
	description?: string
}

defineProps<Props>()
</script>

<template>
	<div
		class="w-full flex flex-col items-center justify-center p-8 text-center rounded-2xl border border-dashed border-white/10 bg-white/[0.02]"
	>
		<div
			v-if="icon"
			class="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center text-[var(--text-muted)] mb-3"
		>
			<component :is="icon" class="w-5 h-5" />
		</div>
		<h3 class="text-sm font-medium text-white m-0">{{ title }}</h3>
		<p v-if="description" class="text-xs text-[var(--text-muted)] mt-1.5 max-w-sm m-0">
			{{ description }}
		</p>
		<div v-if="$slots.action" class="mt-4">
			<slot name="action" />
		</div>
	</div>
</template>
