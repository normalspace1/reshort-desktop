import { onUnmounted } from 'vue'
import { toast } from 'vue-sonner'

import { generationApi, projectsApi, type StartGenerationInput } from '@/api/projects'
import { useProjectStore } from '@/stores/project'
import type { ProjectStatus, VideoInfo } from '@/types/project'
import { statusMessage } from '@/utils/project'

export interface GenerationOptions {
	url: string
	keepMemes: boolean
	uniquify: boolean
	adaptTts?: boolean
	voice?: string
	ttsBaseSpeed?: number
	burnSubtitles?: boolean
}

export interface ResumeSource {
	id: string
	options?: Record<string, unknown>
	info?: Partial<VideoInfo>
}

/**
 * Drives the "add a new video" flow end-to-end: info fetch, start command,
 * and lightweight status polling that resolves the output video or surfaces
 * the failure to the user.
 */
export function useProjectGeneration() {
	const store = useProjectStore()
	let pollTimer: ReturnType<typeof setInterval> | null = null

	async function fetchVideoInfo(url: string): Promise<boolean> {
		store.isFetchingInfo = true
		try {
			store.videoInfo = await generationApi.fetchInfo(url)
			return true
		} catch (e) {
			console.error('fetch_video_info:', e)
			toast.error('Не удалось загрузить информацию о видео')
			return false
		} finally {
			store.isFetchingInfo = false
		}
	}

	async function resolveVideoUrl(projectId: string): Promise<boolean> {
		try {
			const res = await projectsApi.videoUrl(projectId)
			if (res.exists && res.url) {
				store.resultVideoUrl = res.url
				return true
			}
			return false
		} catch (e) {
			console.error('get_video_url:', e)
			return false
		}
	}

	function buildStartInput(options: GenerationOptions): StartGenerationInput {
		const info = store.videoInfo ?? { title: 'Unknown', author: 'Unknown', thumbnail: '' }
		return {
			url: options.url,
			keepMemes: options.keepMemes,
			uniquify: options.uniquify,
			adaptTts: options.adaptTts !== false,
			title: info.title ?? 'Unknown',
			author: info.author ?? 'Unknown',
			thumbnail: info.thumbnail ?? '',
			voice: options.voice,
			ttsBaseSpeed: options.ttsBaseSpeed,
			burnSubtitles: options.burnSubtitles,
		}
	}

	async function startGeneration(options: GenerationOptions): Promise<string | null> {
		store.isProcessing = true
		store.processingMessage = 'Подготовка проекта...'
		store.resultVideoUrl = ''

		try {
			const res = await generationApi.start(buildStartInput(options))
			store.projectId = res.project_id
			await store.loadProjects()
			poll(res.project_id)
			return res.project_id
		} catch (e) {
			console.error('start_generation:', e)
			toast.error('Сбой запуска обработки')
			store.isProcessing = false
			store.processingMessage = ''
			return null
		}
	}

	async function resumeProject(record: ResumeSource) {
		const url = String(record.options?.url ?? '').trim()
		if (!url) {
			toast.error('Недостаточно данных для продолжения')
			return
		}
		store.videoInfo = {
			title: record.info?.title ?? 'Unknown',
			author: record.info?.author ?? 'Unknown',
			thumbnail: record.info?.thumbnail ?? '',
		}
		await startGeneration({
			url,
			keepMemes: record.options?.keep_memes !== false,
			uniquify: record.options?.uniquify !== false,
			adaptTts: record.options?.adapt_tts !== false,
		})
	}

	async function checkStatus(projectId: string) {
		let status: ProjectStatus
		try {
			status = await projectsApi.status(projectId)
		} catch (e) {
			console.error('get_project_status:', e)
			return
		}

		if (status.status === 'running' || status.status === 'queued') {
			store.processingMessage = statusMessage(status)
		} else if (status.status === 'done') {
			stopPolling()
			store.isProcessing = false
			store.processingMessage = ''
			await store.loadProjects()
			const ok = await resolveVideoUrl(projectId)
			if (ok) {
				toast.success('Видео сгенерировано')
			} else {
				toast.error('Файл не найден после генерации')
			}
		} else if (status.status === 'failed' || status.status === 'cancelled') {
			stopPolling()
			store.isProcessing = false
			store.processingMessage = ''
			await store.loadProjects()
			if (status.status === 'cancelled') {
				toast.info('Обработка отменена')
			} else {
				toast.error(
					status.current_stage
						? `Ошибка на этапе "${status.current_stage}"`
						: status.error || 'Ошибка генерации',
				)
			}
		}
	}

	function poll(projectId: string) {
		if (pollTimer) clearInterval(pollTimer)
		pollTimer = setInterval(() => checkStatus(projectId), 2500)
	}

	function stopPolling() {
		if (pollTimer) {
			clearInterval(pollTimer)
			pollTimer = null
		}
	}

	onUnmounted(stopPolling)

	return { fetchVideoInfo, startGeneration, resumeProject }
}
