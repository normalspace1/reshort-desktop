import { defineStore } from 'pinia'
import { computed, ref, shallowRef } from 'vue'
import { toast } from 'vue-sonner'

import { projectsApi } from '@/api/projects'
import { STAGE_NAMES } from '@/constants/project'
import type { ProjectRecord, VideoInfo } from '@/types/project'

export const useProjectStore = defineStore('project', () => {
	const projects = shallowRef<ProjectRecord[]>([])

	// UI Overlays
	const commandPaletteOpen = ref(false)
	const isDraggingFile = ref(false)

	// Transient state of in-flight creation
	const isFetchingInfo = shallowRef(false)
	const videoInfo = shallowRef<VideoInfo | null>(null)
	const isProcessing = shallowRef(false)
	const processingMessage = shallowRef('')
	const resultVideoUrl = shallowRef('')
	const projectId = shallowRef('')

	// Computed counts for the navigation
	const queueCount = computed(
		() => projects.value.filter((p) => p.status === 'queued' || p.status === 'running').length,
	)
	const historyCount = computed(
		() => projects.value.filter((p) => p.status === 'done' || p.status === 'failed').length,
	)

	let syncTimer: ReturnType<typeof setInterval> | null = null
	let isSyncing = false

	async function loadProjects() {
		try {
			const list = await projectsApi.list()

			for (const p of list) {
				const prev = projects.value.find((old) => old.id === p.id)
				if (prev && prev.status !== p.status) {
					if (p.status === 'done') {
						toast.success(`Перевод завершен: ${p.info?.title || p.id}`)
					} else if (p.status === 'failed') {
						const stageLabel = p.current_stage
							? ` на этапе «${STAGE_NAMES[p.current_stage as keyof typeof STAGE_NAMES]}»`
							: ''
						toast.error(`Ошибка${stageLabel}: ${p.error || 'Не удалось выполнить обработку'}`)
					}
				}
			}

			projects.value = list
		} catch (e) {
			console.error('loadProjects:', e)
		}
	}

	async function deleteProject(id: string) {
		await projectsApi.remove(id)
		await loadProjects()
	}

	function getProject(id: string): ProjectRecord | undefined {
		return projects.value.find((p) => p.id === id)
	}

	function syncLoop() {
		if (isSyncing) return
		isSyncing = true
		loadProjects().finally(() => {
			isSyncing = false
		})
	}

	function startRealtimeSync() {
		if (syncTimer) return
		syncLoop()
		syncTimer = setInterval(syncLoop, 1500)
	}

	function stopRealtimeSync() {
		if (syncTimer) {
			clearInterval(syncTimer)
			syncTimer = null
		}
	}

	return {
		projects,
		commandPaletteOpen,
		isDraggingFile,
		queueCount,
		historyCount,
		isFetchingInfo,
		videoInfo,
		isProcessing,
		processingMessage,
		resultVideoUrl,
		projectId,
		loadProjects,
		deleteProject,
		getProject,
		startRealtimeSync,
		stopRealtimeSync,
	}
})
