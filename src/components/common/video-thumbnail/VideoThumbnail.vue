<script setup lang="ts">
import { computed, ref, watch, type HTMLAttributes } from 'vue'
import { Icon } from '@/components/ui'
import { cn } from '@/lib/utils'

interface Props {
	src?: string
	duration?: number
	resolution?: string
	aspectRatio?: 'auto' | 'vertical' | 'horizontal'
	showPlayOnHover?: boolean
	showDuration?: boolean
	class?: HTMLAttributes['class']
}

const props = withDefaults(defineProps<Props>(), {
	aspectRatio: 'auto',
	showPlayOnHover: true,
	showDuration: true,
})

const isVerticalDetected = ref<boolean | null>(null)

watch(
	() => props.resolution,
	(res) => {
		if (res) {
			const [w, h] = res.split('x').map(Number)
			if (w && h) isVerticalDetected.value = h > w
		}
	},
	{ immediate: true },
)

function onImageLoad(e: Event) {
	const img = e.target as HTMLImageElement
	if (img && img.naturalWidth && img.naturalHeight) {
		isVerticalDetected.value = img.naturalHeight > img.naturalWidth
	}
}

const isVertical = computed(() => {
	if (props.aspectRatio === 'vertical') return true
	if (props.aspectRatio === 'horizontal') return false
	if (isVerticalDetected.value !== null) return isVerticalDetected.value
	// Default to vertical 9:16 for Shorts/Reels/TikTok
	return true
})

const formattedDuration = computed(() => {
	if (!props.duration || props.duration <= 0) return ''
	const m = Math.floor(props.duration / 60)
	const s = Math.floor(props.duration % 60)
	return `${m}:${s < 10 ? '0' : ''}${s}`
})
</script>

<template>
	<div
		:class="
			cn(
				'rounded-xl overflow-hidden shrink-0 relative flex items-center justify-center bg-black/60 select-none group',
				isVertical ? 'aspect-[9/16]' : 'aspect-video',
				props.class,
			)
		"
	>
		<!-- Thumbnail Image -->
		<img
			v-if="src"
			:src="src"
			@load="onImageLoad"
			class="w-full h-full object-cover transition-transform group-hover:scale-105"
		/>
		<!-- Fallback Icon -->
		<Icon v-else name="video" class="w-5 h-5 text-white opacity-75" />

		<!-- Duration Badge -->
		<span
			v-if="showDuration && formattedDuration"
			class="absolute bottom-1 right-1 bg-black/85 text-white font-mono text-[9px] px-1 py-0.2 rounded font-medium leading-none pointer-events-none z-10"
		>
			{{ formattedDuration }}
		</span>

		<!-- Hover Play Overlay -->
		<div
			v-if="showPlayOnHover"
			class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity z-10"
		>
			<Icon name="play" class="w-5 h-5 text-white" />
		</div>
	</div>
</template>
