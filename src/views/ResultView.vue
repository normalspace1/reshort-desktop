<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { projectsApi } from '@/api/projects'
import { VideoPlayer } from '@/components/common'
import { Button, Icon } from '@/components/ui'
import { useProjectStore } from '@/stores/project'
import type { ProjectRecord } from '@/types/project'

const route = useRoute()
const router = useRouter()
const store = useProjectStore()

const projectId = computed(() => String(route.params.id ?? ''))
const project = computed<ProjectRecord | undefined>(() =>
	store.projects.find((p) => p.id === projectId.value),
)

const videoUrl = ref<string | null>(null)
const isLoadingVideo = ref(false)

async function loadVideo() {
	if (!projectId.value) return
	isLoadingVideo.value = true
	try {
		const res = await projectsApi.videoUrl(projectId.value)
		videoUrl.value = res.exists && res.url ? res.url : null
	} catch (e) {
		console.error('get_video_url:', e)
		videoUrl.value = null
	} finally {
		isLoadingVideo.value = false
	}
}

watch(projectId, () => loadVideo(), { immediate: true })

async function openFolder() {
	if (!projectId.value) return
	try {
		await projectsApi.openFolder(projectId.value)
	} catch (e) {
		console.error('open_project_folder:', e)
	}
}

onMounted(() => {
	store.loadProjects()
})
</script>

<template>
	<div
		class="w-full flex-1 flex flex-col max-w-md mx-auto items-center justify-center gap-5 py-4 select-none"
	>
		<!-- Верхняя панель -->
		<div class="w-full flex items-center justify-between">
			<button
				type="button"
				@click="router.push({ name: 'history' })"
				class="flex items-center gap-1.5 text-xs text-white hover:opacity-80 bg-transparent border-none cursor-pointer transition-colors p-0"
			>
				<Icon name="arrow-left" class="w-3.5 h-3.5 text-white" />
				<span>История</span>
			</button>

			<span class="text-xs text-[var(--text-muted)] font-mono truncate max-w-[200px]">
				{{ project?.info?.title || projectId }}
			</span>

			<button
				type="button"
				@click="openFolder"
				class="text-white hover:opacity-80 bg-transparent border-none cursor-pointer p-0"
				title="Показать в проводнике"
			>
				<Icon name="folder" class="w-4 h-4 text-white" />
			</button>
		</div>

		<!-- 9:16 Вертикальный фрейм плеера (переиспользуемый VideoPlayer) -->
		<div
			v-if="!videoUrl && isLoadingVideo"
			class="w-full max-w-[280px] aspect-[9/16] rounded-2xl bg-black flex flex-col items-center justify-center text-[var(--text-muted)] gap-2 shadow-2xl"
		>
			<Icon name="video" class="w-8 h-8 text-white" />
			<span class="text-xs">Загрузка видео...</span>
		</div>
		<VideoPlayer v-else-if="videoUrl" :src="videoUrl" />
		<div
			v-else
			class="w-full max-w-[280px] aspect-[9/16] rounded-2xl bg-black flex flex-col items-center justify-center text-[var(--text-muted)] gap-2 shadow-2xl"
		>
			<Icon name="video" class="w-8 h-8 text-white" />
			<span class="text-xs">Файл видео не найден</span>
		</div>

		<!-- Действия: Скачать MP4 / Новый дубляж (Shadcn Buttons) -->
		<div class="flex items-center gap-2 w-full max-w-[280px]">
			<a v-if="videoUrl" :href="videoUrl" download="dubbed.mp4" class="flex-1 no-underline">
				<Button class="w-full gap-2">
					<Icon name="download" class="w-3.5 h-3.5" />
					<span>Скачать MP4</span>
				</Button>
			</a>

			<Button
				variant="secondary"
				size="icon"
				@click="router.push({ name: 'queue' })"
				title="Перевести новое видео"
			>
				<Icon name="reload" class="w-4 h-4 text-white" />
			</Button>
		</div>
	</div>
</template>
