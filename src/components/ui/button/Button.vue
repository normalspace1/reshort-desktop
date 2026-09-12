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
		default: 'bg-white text-[#0f0f0f] font-medium hover:bg-[#e5e5e5] active:bg-[#cccccc]',
		secondary: 'bg-white/10 text-white font-medium hover:bg-white/20 active:bg-white/30',
		ghost: 'bg-transparent text-[var(--text-secondary)] hover:text-white hover:bg-white/10',
		outline: 'bg-transparent text-[var(--text-primary)] hover:bg-white/10',
		destructive: 'bg-red-500/20 text-red-300 hover:bg-red-500/30',
	}

	const sizes = {
		default: 'h-9 px-4 py-2 text-xs rounded-full',
		sm: 'h-8 px-3.5 text-xs rounded-full',
		lg: 'h-10 px-5 text-sm rounded-full',
		icon: 'h-8 w-8 p-0 flex items-center justify-center rounded-full',
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
