<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { toast } from 'vue-sonner'
import { projectsApi } from '@/api/projects'
import { VideoThumbnail } from '@/components/common'
import { Button, Icon, Progress } from '@/components/ui'
import { useProjectGeneration } from '@/composables/useProjectGeneration'
import { STAGE_NAMES, STAGE_ORDER } from '@/constants/project'
import { useProjectStore } from '@/stores/project'
import type { ProjectRecord, StageName } from '@/types/project'
import { getStageState } from '@/utils/project'

const route = useRoute()
const router = useRouter()
const store = useProjectStore()
const { resumeProject } = useProjectGeneration()

const projectId = computed(() => String(route.params.id ?? ''))

const project = computed<ProjectRecord | undefined>(() =>
	store.projects.find((p) => p.id === projectId.value),
)

watch(
	() => project.value?.status,
	(newStatus) => {
		if (newStatus === 'done') {
			toast.success('Дубляж успешно завершен!')
		}
	},
)

const currentStageIndex = computed(() => {
	if (!project.value?.current_stage) return 0
	const idx = STAGE_ORDER.indexOf(project.value.current_stage as StageName)
	return idx >= 0 ? idx : 0
})

const overallProgress = computed(() => {
	if (project.value?.status === 'done') return 100
	if (project.value?.status === 'failed') return currentStageIndex.value * 14
	const base = currentStageIndex.value * 14
	return Math.min(Math.round(base + 10), 96)
})

const estimatedRemainingSeconds = computed(() => {
	if (project.value?.status === 'done') return 0
	const remainingStages = STAGE_ORDER.length - currentStageIndex.value
	return Math.max(remainingStages * 5, 4)
})

async function handleRetry() {
	if (!project.value) return
	toast.info('Повторный запуск...')
	await resumeProject(project.value)
}

async function openFolder() {
	if (!projectId.value) return
	try {
		await projectsApi.openFolder(projectId.value)
	} catch (e) {
		console.error(e)
	}
}

onMounted(() => {
	store.loadProjects()
})
</script>

<template>
	<div class="w-full flex-1 flex flex-col max-w-5xl gap-6 select-none">
		<!-- Унифицированный заголовок страницы -->
		<div class="flex items-center justify-between gap-4">
			<div class="flex items-center gap-3 min-w-0">
				<button
					type="button"
					@click="router.push({ name: 'queue' })"
					class="p-2 -ml-2 rounded-full hover:bg-white/10 text-white bg-transparent border-none cursor-pointer transition-colors flex items-center justify-center shrink-0"
					title="Назад на главную"
				>
					<Icon name="arrow-left" class="w-4 h-4 text-white" />
				</button>
				<div class="min-w-0">
					<h1 class="text-base font-semibold text-white tracking-tight m-0">Обработка видео</h1>
					<p class="text-xs text-[var(--text-secondary)] mt-0.5 m-0 truncate">
						{{ project?.info?.title || projectId }}
					</p>
				</div>
			</div>

			<button
				type="button"
				@click="openFolder"
				class="p-2 rounded-full hover:bg-white/10 text-white bg-transparent border-none cursor-pointer transition-colors flex items-center justify-center shrink-0"
				title="Открыть папку с файлами"
			>
				<Icon name="folder" class="w-4 h-4 text-white" />
			</button>
		</div>

		<!-- Карточка процесса обработки -->
		<div class="w-full max-w-md mx-auto flex flex-col items-center justify-center gap-6 py-4">
			<!-- Адаптивное превью через VideoThumbnail -->
			<div class="w-full max-w-[260px] relative">
				<VideoThumbnail
					:src="project?.info?.thumbnail"
					:duration="project?.info?.duration"
					:resolution="project?.info?.resolution"
					:show-play-on-hover="false"
					:show-duration="false"
					class="w-full shadow-lg"
				>
					<!-- Анимированный спиннер во время обработки -->
					<div
						v-if="project?.status === 'running'"
						class="absolute inset-0 bg-black/40 flex flex-col items-center justify-center gap-2 z-10"
					>
						<Icon name="reload" class="w-7 h-7 animate-spin text-white" />
					</div>

					<!-- Иконка воспроизведения при готовности -->
					<div
						v-else-if="project?.status === 'done'"
						class="absolute inset-0 flex items-center justify-center bg-black/40 cursor-pointer z-10"
						@click="router.push({ name: 'result', params: { id: projectId } })"
					>
						<Icon
							name="play"
							class="w-14 h-14 text-white drop-shadow-xl transition-transform hover:scale-110"
						/>
					</div>
				</VideoThumbnail>
			</div>

			<!-- Статус и процент выполнения -->
			<div class="w-full flex flex-col items-center gap-3 text-center">
				<div class="flex items-center gap-2">
					<span class="text-sm font-semibold text-white">
						{{
							project?.status === 'done'
								? 'Готово'
								: project?.current_stage
									? STAGE_NAMES[project.current_stage as StageName]
									: 'Обработка...'
						}}
					</span>
					<span class="text-xs font-mono text-white font-medium"> {{ overallProgress }}% </span>
				</div>

				<!-- Shadcn Progress bar -->
				<div class="w-full max-w-sm">
					<Progress :model-value="overallProgress" />
				</div>

				<!-- Горизонтальная цепочка этапов -->
				<div class="flex items-center gap-1.5 mt-2 flex-wrap justify-center text-[10px] font-mono">
					<template v-for="(stage, idx) in STAGE_ORDER" :key="stage">
						<span
							:class="{
								'text-white font-semibold animate-pulse':
									getStageState(project, stage) === 'running',
								'text-white/80': getStageState(project, stage) === 'done',
								'text-[var(--text-muted)]': getStageState(project, stage) === 'queued',
							}"
						>
							{{ STAGE_NAMES[stage] }}
						</span>
						<span v-if="idx < STAGE_ORDER.length - 1" class="text-[var(--text-disabled)]">·</span>
					</template>
				</div>

				<span
					v-if="project?.status === 'running'"
					class="text-[11px] font-mono text-[var(--text-muted)] mt-1"
				>
					Осталось ~{{ estimatedRemainingSeconds }} сек
				</span>

				<!-- Статус фоновой работы (психологический комфорт) -->
				<div
					v-if="project?.status === 'running'"
					class="flex items-center gap-2 px-3.5 py-1.5 mt-2 rounded-full bg-white/5 text-[11px] text-[var(--text-secondary)] select-none"
				>
					<Icon name="info" class="w-3.5 h-3.5 text-white opacity-60 shrink-0" />
					<span>Фоновый процесс: можно ставить следующие видео в очередь</span>
				</div>
			</div>

			<!-- Кнопки действий при завершении или ошибке -->
			<div v-if="project?.status === 'done'" class="mt-2">
				<Button
					@click="router.push({ name: 'result', params: { id: projectId } })"
					class="gap-2 active:scale-[0.98] transition-transform"
				>
					<span>Смотреть результат</span>
					<Icon name="arrow-right" class="w-3.5 h-3.5 text-black" />
				</Button>
			</div>

			<div v-else-if="project?.status === 'failed'" class="flex items-center gap-3">
				<span class="text-xs text-[#f87171] font-medium">Не удалось завершить</span>
				<Button
					variant="secondary"
					size="sm"
					@click="handleRetry"
					class="gap-1.5 active:scale-[0.98] transition-transform"
				>
					<Icon name="reload" class="w-3.5 h-3.5 text-white" />
					<span>Повторить</span>
				</Button>
			</div>
		</div>
	</div>
</template>
