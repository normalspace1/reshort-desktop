export interface VideoInfo {
	title: string
	author: string
	thumbnail: string
	duration?: number
	resolution?: string
	sizeBytes?: number
}

export type ProjectStatusName = 'queued' | 'running' | 'done' | 'failed' | 'cancelled' | 'paused'

export type StageName =
	'download' | 'separate' | 'transcribe' | 'translate' | 'tts' | 'mix' | 'finalize'

export type ProjectStageStatus = 'queued' | 'running' | 'done' | 'skipped' | 'failed'

export interface ProjectStage {
	status: ProjectStageStatus
	error?: string
	result?: Record<string, unknown>
	progress?: number
	message?: string
}

export interface ProjectInfo {
	title?: string
	author?: string
	thumbnail?: string
	duration?: number
	resolution?: string
	sizeBytes?: number
}

export interface ProjectOptions {
	url?: string
	voice?: string
	voice_id?: string
	tts_base_speed?: number
	burn_subtitles?: boolean
	keep_memes?: boolean
	uniquify?: boolean
	adapt_tts?: boolean
	source_lang?: string
	target_lang?: string
	[key: string]: unknown
}

export interface ProjectStatus {
	id: string
	status: ProjectStatusName
	current_stage?: string
	progress?: number
	error?: string
	created_at?: string
	info?: ProjectInfo
	stages?: Record<string, ProjectStage>
}

export interface ProjectRecord extends ProjectStatus {
	has_video?: boolean
	options?: ProjectOptions
}

export interface Preset {
	id: string
	name: string
	description: string
	voice: string
	speed: number
	smartAdaptation: boolean
	musicPreservation: boolean
	smartDucking: boolean
	shortsSubtitles: boolean
	burnSubtitles: boolean
	targetLang: string
}
