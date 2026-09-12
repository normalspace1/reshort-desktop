<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { computed } from 'vue'
import { cn } from '@/lib/utils'

interface Props {
	variant?: 'default' | 'secondary' | 'ghost' | 'outline' | 'destructive'
	size?: 'default' | 'sm' | 'lg' | 'icon'
	class?: HTMLAttributes['class']
	disabled?: boolean
	type?: 'button' | 'submit' | 'reset'
}

const props = withDefaults(defineProps<Props>(), {
	variant: 'default',
	size: 'default',
	type: 'button',
})

const variantClasses = computed(() => {
	const variants = {
		default:
			'bg-[var(--accent)] text-[var(--accent-text)] font-semibold hover:bg-[var(--accent-hover)] active:scale-[0.98] shadow-sm',
		secondary:
			'bg-[var(--bg-secondary)] text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] active:scale-[0.98]',
		ghost: 'bg-transparent text-[var(--text-muted)] hover:text-white hover:bg-[var(--bg-tertiary)]',
		outline:
			'border border-white/10 bg-transparent text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)]',
		destructive: 'bg-red-500/15 text-red-400 hover:bg-red-500/25',
	}

	const sizes = {
		default: 'h-9 px-4 py-2 text-xs rounded-xl',
		sm: 'h-8 px-3 text-xs rounded-lg',
		lg: 'h-10 px-5 text-sm rounded-xl',
		icon: 'h-8 w-8 p-0 flex items-center justify-center rounded-lg',
	}

	return cn(
		'inline-flex items-center justify-center whitespace-nowrap font-medium transition-all select-none border-none outline-none cursor-pointer disabled:pointer-events-none disabled:opacity-50',
		variants[props.variant],
		sizes[props.size],
		props.class,
	)
})
</script>

<template>
	<button :type="type" :disabled="disabled" :class="variantClasses">
		<slot />
	</button>
</template>
