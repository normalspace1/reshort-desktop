<script setup lang="ts">
import { computed, type HTMLAttributes } from 'vue'
import { cn } from '@/lib/utils'

// Eager load all SVG raw contents from src/assets/icons/
const iconModules = import.meta.glob('@/assets/icons/*.svg', {
	query: '?raw',
	import: 'default',
	eager: true,
}) as Record<string, string>

// Map 'play', 'play.svg' or any case to raw SVG markup
const iconsMap = new Map<string, string>()

for (const [path, rawSvg] of Object.entries(iconModules)) {
	const filename = path.split(/[/\\]/).pop() || ''
	const nameWithoutExt = filename.replace(/\.svg$/i, '').toLowerCase()

	let normalized = rawSvg
		.replace(/<\?xml.*?\?>/gi, '')
		.replace(/<!DOCTYPE.*?>/gi, '')
		.replace(/fill="(?:#000|#000000|#fff|#ffffff|#aaa|black|white)"/gi, 'fill="currentColor"')
		.replace(
			/style="([^"]*?)fill:\s*(?:#000|#000000|#fff|#ffffff|#aaa|black|white)(;?)"/gi,
			'style="$1fill:currentColor$2"',
		)
		.replace(/style="([^"]*?)color:\s*#000(;?)"/gi, 'style="$1$2"')

	if (!normalized.includes('viewBox=') && !normalized.includes('viewbox=')) {
		const widthMatch = normalized.match(/width="(\d+)"/)
		const heightMatch = normalized.match(/height="(\d+)"/)
		if (widthMatch && heightMatch) {
			const w = widthMatch[1]
			const h = heightMatch[1]
			normalized = normalized.replace('<svg', `<svg viewBox="0 0 ${w} ${h}"`)
		}
	}

	normalized = normalized.replace(/<svg\b([^>]*)>/i, (_match, attrs) => {
		const cleanedAttrs = attrs.replace(/\s*width="[^"]*"/gi, '').replace(/\s*height="[^"]*"/gi, '')
		return `<svg class="w-full h-full block" fill="currentColor"${cleanedAttrs}>`
	})

	iconsMap.set(nameWithoutExt, normalized)
}

interface Props {
	name: string
	class?: HTMLAttributes['class']
}

const props = defineProps<Props>()

const svgContent = computed(() => {
	const key = props.name.toLowerCase().replace(/\.svg$/, '')
	return iconsMap.get(key) || null
})
</script>

<template>
	<span
		v-if="svgContent"
		:class="
			cn(
				'inline-flex items-center justify-center shrink-0 w-4 h-4 text-current transition-colors fill-current',
				props.class,
			)
		"
		v-html="svgContent"
		aria-hidden="true"
	/>
	<span
		v-else
		:class="cn('inline-block w-4 h-4 bg-white/10 rounded', props.class)"
		:title="`Icon not found: ${name}`"
	/>
</template>
