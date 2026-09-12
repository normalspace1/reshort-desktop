<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'

interface Props {
	class?: HTMLAttributes['class']
}

defineProps<Props>()
</script>

<template>
	<kbd
		:class="
			cn(
				'pointer-events-none inline-flex h-5 select-none items-center gap-1 rounded border border-white/10 bg-white/5 px-1.5 font-mono text-[10px] font-medium text-[var(--text-muted)]',
				$props.class,
			)
		"
	>
		<slot />
	</kbd>
</template>
