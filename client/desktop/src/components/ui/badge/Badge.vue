<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { computed } from 'vue'
import { cn } from '@/lib/utils'

interface Props {
	variant?: 'default' | 'secondary' | 'accent' | 'destructive' | 'outline'
	class?: HTMLAttributes['class']
}

const props = withDefaults(defineProps<Props>(), {
	variant: 'default',
})

const classes = computed(() => {
	const variants = {
		default: 'bg-[var(--bg-tertiary)] text-white',
		secondary: 'bg-[var(--bg-secondary)] text-[var(--text-secondary)]',
		accent: 'bg-[var(--accent-subtle)] text-[var(--accent)]',
		destructive: 'bg-red-500/15 text-red-400',
		outline: 'border border-white/10 text-white',
	}

	return cn(
		'inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[10px] font-mono font-medium transition-colors select-none',
		variants[props.variant],
		props.class,
	)
})
</script>

<template>
	<span :class="classes">
		<slot />
	</span>
</template>
