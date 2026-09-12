<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { computed } from 'vue'
import { useVModel } from '@vueuse/core'
import { cn } from '@/lib/utils'

interface Props {
	defaultValue?: string | number
	modelValue?: string | number
	class?: HTMLAttributes['class']
	placeholder?: string
	type?: string
	disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
	type: 'text',
})

const emits = defineEmits<{
	(e: 'update:modelValue', payload: string | number): void
}>()

const modelValue = useVModel(props, 'modelValue', emits, {
	passive: true,
	defaultValue: props.defaultValue,
})

const classes = computed(() =>
	cn(
		'flex h-9 w-full rounded-xl bg-[var(--bg-secondary)] px-3 py-1 text-xs text-white placeholder:text-[var(--text-muted)] focus-visible:outline-none border-none transition-colors disabled:cursor-not-allowed disabled:opacity-50',
		props.class,
	),
)
</script>

<template>
	<input
		v-model="modelValue"
		:type="type"
		:placeholder="placeholder"
		:disabled="disabled"
		:class="classes"
	/>
</template>
