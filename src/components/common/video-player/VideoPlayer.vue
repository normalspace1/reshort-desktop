<script setup lang="ts">
import { ref } from 'vue'
import { Icon } from '@/components/ui'

interface Props {
	src: string
	poster?: string
	autoplay?: boolean
	loop?: boolean
}

const props = withDefaults(defineProps<Props>(), {
	autoplay: false,
	loop: false,
})

const videoRef = ref<HTMLVideoElement | null>(null)
const isPlaying = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const isMuted = ref(false)

function togglePlay() {
	if (!videoRef.value) return
	if (videoRef.value.paused) {
		videoRef.value.play()
		isPlaying.value = true
	} else {
		videoRef.value.pause()
		isPlaying.value = false
	}
}

function handleTimeUpdate() {
	if (!videoRef.value) return
	currentTime.value = videoRef.value.currentTime
	duration.value = videoRef.value.duration || 0
}

function handleSeek(e: Event) {
	const val = Number((e.target as HTMLInputElement).value)
	if (videoRef.value) {
		videoRef.value.currentTime = val
		currentTime.value = val
	}
}

function toggleMute() {
	if (!videoRef.value) return
	videoRef.value.muted = !videoRef.value.muted
	isMuted.value = videoRef.value.muted
}

function toggleFullscreen() {
	if (!videoRef.value) return
	if (document.fullscreenElement) {
		document.exitFullscreen()
	} else {
		videoRef.value.requestFullscreen()
	}
}

function formatTime(secs: number): string {
	if (!secs || isNaN(secs)) return '00:00'
	const m = Math.floor(secs / 60)
	const s = Math.floor(secs % 60)
	return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

defineExpose({
	videoRef,
	togglePlay,
	toggleMute,
})
</script>

<template>
	<div
		class="relative aspect-[9/16] w-full max-w-[280px] rounded-2xl overflow-hidden shadow-2xl bg-black border border-white/10 group select-none flex items-center justify-center"
	>
		<video
			ref="videoRef"
			:src="src"
			:poster="poster"
			:loop="loop"
			@timeupdate="handleTimeUpdate"
			@loadedmetadata="handleTimeUpdate"
			@play="isPlaying = true"
			@pause="isPlaying = false"
			@click="togglePlay"
			class="w-full h-full object-contain cursor-pointer"
			playsinline
		/>

		<!-- Центральная кнопка Play/Pause (при паузе) -->
		<button
			v-if="!isPlaying"
			type="button"
			@click="togglePlay"
			class="absolute inset-0 m-auto w-14 h-14 rounded-full bg-black/60 backdrop-blur-md border border-white/20 flex items-center justify-center text-white cursor-pointer hover:scale-110 active:scale-95 transition-all z-10"
		>
			<Icon name="play" class="w-6 h-6 ml-0.5 text-white" />
		</button>

		<!-- Панель управления видео (всплывает при наведении) -->
		<div
			class="absolute inset-x-0 bottom-0 p-3 pt-8 bg-gradient-to-t from-black/90 via-black/40 to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex flex-col gap-1.5 z-20"
		>
			<!-- Скруббер таймлайна -->
			<input
				type="range"
				min="0"
				:max="duration || 100"
				step="0.05"
				:value="currentTime"
				@input="handleSeek"
				class="w-full h-1 bg-white/20 rounded-lg appearance-none cursor-pointer accent-[var(--accent)] hover:h-1.5 transition-all"
			/>

			<!-- Кнопки управления -->
			<div class="flex items-center justify-between text-xs text-white">
				<div class="flex items-center gap-2">
					<button
						type="button"
						@click="togglePlay"
						class="text-white hover:text-[var(--accent)] bg-transparent border-none cursor-pointer p-0"
					>
						<Icon :name="isPlaying ? 'pause' : 'play'" class="w-4 h-4 text-white" />
					</button>

					<button
						type="button"
						@click="toggleMute"
						class="text-white hover:text-[var(--accent)] bg-transparent border-none cursor-pointer p-0"
					>
						<Icon :name="isMuted ? 'muted' : 'volume-2'" class="w-4 h-4 text-white" />
					</button>

					<span class="text-[10px] font-mono text-[var(--text-muted)]">
						{{ formatTime(currentTime) }} / {{ formatTime(duration) }}
					</span>
				</div>

				<button
					type="button"
					@click="toggleFullscreen"
					class="text-white hover:text-[var(--accent)] bg-transparent border-none cursor-pointer p-0"
				>
					<Icon name="fullscreen" class="w-3.5 h-3.5 text-white" />
				</button>
			</div>
		</div>
	</div>
</template>
