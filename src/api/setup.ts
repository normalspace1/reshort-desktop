import { invoke } from '@/api/tauri'

import type { PreflightItem } from '@/types/setup'

export interface SetupProgress {
	item: string
	status: string
	done?: number
	total?: number
}

export interface SetupSnapshot {
	running: boolean
	item: string
	status: string
	done: number
	total?: number | null
}

export const setupApi = {
	start: () => invoke<void>('setup_start'),

	check: () => invoke<PreflightItem[]>('preflight_check'),

	progress: () => invoke<SetupSnapshot>('preflight_progress'),

	retry: () => invoke<PreflightItem[]>('preflight_retry'),
}
