<script setup lang="ts">
import { onMounted, onUnmounted, shallowRef } from 'vue'
import { useRouter } from 'vue-router'
import { UploadCloudIcon } from '@lucide/vue'

import { CommandPalette, Sonner, TopNav } from '@/components/common'
import { useProjectStore } from '@/stores/project'
import LaunchView from '@/views/LaunchView.vue'

const setupDone = shallowRef(false)
const router = useRouter()
const store = useProjectStore()

function isScrollable(el: HTMLElement | null, vertical: boolean): boolean {
	const axis = vertical ? 'overflowY' : 'overflowX'
	while (el) {
		const overflow = getComputedStyle(el)[axis]
		const canScroll =
			(overflow === 'auto' || overflow === 'scroll') &&
			(vertical ? el.scrollHeight > el.clientHeight : el.scrollWidth > el.clientWidth)
		if (canScroll) return true
		el = el.parentElement
	}
	return false
}

const blockPan = (e: WheelEvent) => {
	const vertical = Math.abs(e.deltaY) > Math.abs(e.deltaX)
	if (!isScrollable(e.target as HTMLElement | null, vertical)) {
		e.preventDefault()
	}
}

function handleGlobalKeydown(e: KeyboardEvent) {
	if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
		e.preventDefault()
		store.commandPaletteOpen = !store.commandPaletteOpen
	} else if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'n') {
		e.preventDefault()
		router.push({ name: 'queue' })
	}
}

// Drag & Drop events
function handleDragEnter(e: DragEvent) {
	e.preventDefault()
	store.isDraggingFile = true
}

function handleDragOver(e: DragEvent) {
	e.preventDefault()
	store.isDraggingFile = true
}

function handleDragLeave(e: DragEvent) {
	e.preventDefault()
	if (e.relatedTarget === null) {
		store.isDraggingFile = false
	}
}

function handleDrop(e: DragEvent) {
	e.preventDefault()
	store.isDraggingFile = false
	router.push({ name: 'queue' })
}

onMounted(() => {
	store.startRealtimeSync()
	window.addEventListener('wheel', blockPan, { passive: false })
	window.addEventListener('keydown', handleGlobalKeydown)
	window.addEventListener('dragenter', handleDragEnter)
	window.addEventListener('dragover', handleDragOver)
	window.addEventListener('dragleave', handleDragLeave)
	window.addEventListener('drop', handleDrop)
})

onUnmounted(() => {
	store.stopRealtimeSync()
	window.removeEventListener('wheel', blockPan)
	window.removeEventListener('keydown', handleGlobalKeydown)
	window.removeEventListener('dragenter', handleDragEnter)
	window.removeEventListener('dragover', handleDragOver)
	window.removeEventListener('dragleave', handleDragLeave)
	window.removeEventListener('drop', handleDrop)
})
</script>

<template>
	<div
		class="flex flex-col h-screen w-full overflow-hidden select-none"
		style="background-color: var(--bg-primary); color: var(--text-primary)"
	>
		<!-- Launch screen (preflight) -->
		<div v-if="!setupDone" class="flex-1 min-h-0">
			<LaunchView @ready="setupDone = true" />
		</div>

		<!-- Main app (after setup) -->
		<div v-else class="flex flex-col flex-1 min-h-0 w-full">
			<!-- macOS-style Top Navigation Bar -->
			<TopNav />

			<!-- Main Content Area (Full width) -->
			<main
				class="flex-1 overflow-y-auto relative flex flex-col w-full"
				style="background-color: var(--bg-primary)"
			>
				<!-- Routed content -->
				<div class="w-full flex-1 flex flex-col px-8 pb-8 pt-2">
					<router-view v-slot="{ Component }">
						<KeepAlive>
							<component :is="Component" />
						</KeepAlive>
					</router-view>
				</div>
			</main>
		</div>

		<!-- Global Command Palette Modal (⌘K) -->
		<CommandPalette v-if="store.commandPaletteOpen" @close="store.commandPaletteOpen = false" />

		<!-- Global Drag & Drop Overlay -->
		<div
			v-if="store.isDraggingFile"
			class="fixed inset-0 z-50 flex items-center justify-center p-8 pointer-events-none"
			style="background: rgba(8, 8, 8, 0.85); backdrop-filter: blur(10px)"
		>
			<div
				class="w-full max-w-lg aspect-video rounded-3xl border-2 border-dashed flex flex-col items-center justify-center gap-4 text-center"
				style="border-color: var(--accent); background: rgba(16, 16, 16, 0.9)"
			>
				<div
					class="w-16 h-16 rounded-2xl flex items-center justify-center"
					style="background: var(--accent-subtle)"
				>
					<UploadCloudIcon class="w-8 h-8 text-[var(--accent)]" />
				</div>
				<div>
					<h3 class="text-base font-semibold text-white">Перетащите видео или папку сюда</h3>
					<p class="text-xs text-[var(--text-muted)] mt-1">
						Поддерживаются .mp4, .mov, .mkv, .webm или папки с роликами
					</p>
				</div>
			</div>
		</div>

		<!-- Toasts container -->
		<Sonner position="bottom-right" theme="dark" />
	</div>
</template>
