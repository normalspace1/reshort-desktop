<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { computed } from 'vue'
import { cn } from '@/lib/utils'

interface Props {
	modelValue?: number
	max?: number
	class?: HTMLAttributes['class']
}

const props = withDefaults(defineProps<Props>(), {
	modelValue: 0,
	max: 100,
})

const percentage = computed(() => Math.min(Math.max((props.modelValue / props.max) * 100, 0), 100))

const classes = computed(() =>
	cn('relative h-1 w-full overflow-hidden rounded-full bg-[var(--bg-secondary)]', props.class),
)
</script>

<template>
	<div :class="classes">
		<div
			class="h-full w-full flex-1 bg-[var(--accent)] transition-all duration-500 ease-out"
			:style="{ transform: `translateX(-${100 - percentage}%)` }"
		/>
	</div>
</template>
