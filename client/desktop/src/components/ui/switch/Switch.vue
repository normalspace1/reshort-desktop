<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'

interface Props {
	modelValue?: boolean
	disabled?: boolean
	class?: HTMLAttributes['class']
}

const props = withDefaults(defineProps<Props>(), {
	modelValue: false,
	disabled: false,
})

const emit = defineEmits<{
	(e: 'update:modelValue', value: boolean): void
}>()

function toggle() {
	if (!props.disabled) {
		emit('update:modelValue', !props.modelValue)
	}
}
</script>

<template>
	<button
		type="button"
		role="switch"
		:aria-checked="modelValue"
		:disabled="disabled"
		@click="toggle"
		:class="
			cn(
				'inline-flex h-5 w-9 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[var(--accent)] disabled:cursor-not-allowed disabled:opacity-50 p-0',
				modelValue ? 'bg-[var(--accent)]' : 'bg-white/10 hover:bg-white/15',
				props.class,
			)
		"
	>
		<span
			:class="
				cn(
					'pointer-events-none block h-4 w-4 rounded-full shadow-sm transition-transform',
					modelValue ? 'translate-x-4 bg-black' : 'translate-x-0 bg-white/70',
				)
			"
		/>
	</button>
</template>
