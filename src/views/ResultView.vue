<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { toast } from 'vue-sonner'
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

const isCopied = ref(false)

async function handleCopyLink() {
	if (!videoUrl.value) return
	try {
		await navigator.clipboard.writeText(videoUrl.value)
		isCopied.value = true
		toast.success('Ссылка на видео скопирована')
		setTimeout(() => {
			isCopied.value = false
		}, 2000)
	} catch {
		toast.error('Не удалось скопировать')
	}
}

onMounted(() => {
	store.loadProjects()
})
</script>

<template>
	<div class="w-full flex-1 flex flex-col max-w-4xl mx-auto gap-6 select-none">
		<!-- Унифицированный заголовок страницы -->
		<div class="flex items-center justify-between gap-4">
			<div class="flex items-center gap-3 min-w-0">
				<button
					type="button"
					@click="router.push({ name: 'history' })"
					class="p-2 -ml-2 rounded-full hover:bg-white/10 text-white bg-transparent border-none cursor-pointer transition-colors flex items-center justify-center shrink-0"
					title="Назад к контенту"
				>
					<Icon name="arrow-left" class="w-4 h-4 text-white" />
				</button>
				<div class="min-w-0">
					<h1 class="text-base font-semibold text-white tracking-tight m-0">Готовое видео</h1>
					<p class="text-xs text-[var(--text-secondary)] mt-0.5 m-0 truncate">
						{{ project?.info?.title || projectId }}
					</p>
				</div>
			</div>

			<button
				type="button"
				@click="openFolder"
				class="p-2 rounded-full hover:bg-white/10 text-white bg-transparent border-none cursor-pointer transition-colors flex items-center justify-center shrink-0"
				title="Показать в проводнике"
			>
				<Icon name="folder" class="w-4 h-4 text-white" />
			</button>
		</div>

		<!-- Карточка плеера и скачивания (по центру) -->
		<div class="w-full max-w-md mx-auto flex flex-col items-center justify-center gap-5 py-4">
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

			<!-- Действия: Скачать MP4 / Копировать ссылку / Новый дубляж -->
			<div class="flex items-center gap-2 w-full max-w-[280px]">
				<a v-if="videoUrl" :href="videoUrl" download="dubbed.mp4" class="flex-1 no-underline">
					<Button class="w-full gap-2 active:scale-[0.98] transition-transform">
						<Icon name="download" class="w-3.5 h-3.5 text-black" />
						<span>Скачать MP4</span>
					</Button>
				</a>

				<Button
					v-if="videoUrl"
					variant="secondary"
					size="icon"
					@click="handleCopyLink"
					class="shrink-0 active:scale-[0.96] transition-transform"
					title="Скопировать ссылку на видео"
				>
					<Icon :name="isCopied ? 'check' : 'copy'" class="w-4 h-4 text-white" />
				</Button>

				<Button
					variant="secondary"
					size="icon"
					@click="router.push({ name: 'queue' })"
					class="shrink-0 active:scale-[0.96] transition-transform"
					title="Перевести новое видео"
				>
					<Icon name="reload" class="w-4 h-4 text-white" />
				</Button>
			</div>
		</div>
	</div>
</template>
