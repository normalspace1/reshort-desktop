import { invoke } from '@/api/tauri'

import type { ProjectRecord, ProjectStatus, VideoInfo } from '@/types/project'

export interface VideoFileUrl {
	url: string | null
	exists: boolean
}

export interface StartGenerationInput {
	url: string
	keepMemes: boolean
	uniquify: boolean
	adaptTts: boolean
	title: string
	author: string
	thumbnail: string
	voice?: string
	ttsBaseSpeed?: number
	burnSubtitles?: boolean
}

export interface StartLocalGenerationInput {
	filePath: string
	voice?: string
	ttsBaseSpeed?: number
	burnSubtitles?: boolean
	keepMemes?: boolean
	uniquify?: boolean
	adaptTts?: boolean
}

export interface StartBatchGenerationInput {
	filePaths: string[]
	voice?: string
	ttsBaseSpeed?: number
	burnSubtitles?: boolean
	keepMemes?: boolean
	uniquify?: boolean
	adaptTts?: boolean
}

export const projectsApi = {
	list: () => invoke<ProjectRecord[]>('list_projects'),

	status: (projectId: string) => invoke<ProjectStatus>('get_project_status', { projectId }),

	videoUrl: (projectId: string) => invoke<VideoFileUrl>('get_video_url', { projectId }),

	/** Delete a project and its local files. */
	remove: (projectId: string) => invoke<Record<string, unknown>>('delete_project', { projectId }),

	openFolder: (projectId: string) =>
		invoke<Record<string, unknown>>('open_project_folder', { projectId }),
}

export const filePickerApi = {
	pickFile: () => invoke<string | null>('pick_video_file'),
	pickFolder: () => invoke<string | null>('pick_video_folder'),
	scanFolder: (folder: string) => invoke<string[]>('scan_folder_videos', { folder }),
}

export const generationApi = {
	fetchInfo: (url: string) => invoke<VideoInfo>('fetch_video_info', { url }),

	start: (input: StartGenerationInput) =>
		invoke<{ project_id: string; status: string }>('start_generation', {
			url: input.url,
			keep_memes: input.keepMemes,
			uniquify: input.uniquify,
			adapt_tts: input.adaptTts,
			voice: input.voice,
			tts_base_speed: input.ttsBaseSpeed,
			burn_subtitles: input.burnSubtitles,
			title: input.title,
			author: input.author,
			thumbnail: input.thumbnail,
		}),

	startLocal: (input: StartLocalGenerationInput) =>
		invoke<{ project_id: string; status: string }>('start_local_generation', {
			file_path: input.filePath,
			voice: input.voice,
			tts_base_speed: input.ttsBaseSpeed,
			burn_subtitles: input.burnSubtitles,
			keep_memes: input.keepMemes,
			uniquify: input.uniquify,
			adapt_tts: input.adaptTts,
		}),

	startBatch: (input: StartBatchGenerationInput) =>
		invoke<{ started_count: number; project_ids: string[] }>('start_batch_generation', {
			file_paths: input.filePaths,
			voice: input.voice,
			tts_base_speed: input.ttsBaseSpeed,
			burn_subtitles: input.burnSubtitles,
			keep_memes: input.keepMemes,
			uniquify: input.uniquify,
			adapt_tts: input.adaptTts,
		}),
}
