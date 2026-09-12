import { STAGE_NAMES, STAGE_ORDER } from '@/constants/project'

import type {
	ProjectRecord,
	ProjectStageStatus,
	ProjectStatusName,
	StageName,
} from '@/types/project'

export interface StageProgress {
	percent: number
	stageLabel: string
}

export function statusMessage(status: {
	status: ProjectStatusName
	current_stage?: string
}): string {
	if (status.status !== 'running' && status.status !== 'queued') return ''
	return STAGE_ORDER.includes(status.current_stage as StageName)
		? `${STAGE_NAMES[status.current_stage as StageName]}...`
		: 'Обработка...'
}

export function statusColor(status: ProjectStatusName): string {
	switch (status) {
		case 'done':
			return 'var(--success)'
		case 'failed':
			return 'var(--error)'
		case 'running':
		case 'queued':
			return 'var(--accent)'
		default:
			return 'var(--text-muted)'
	}
}

export function getStageProgress(project: ProjectRecord): StageProgress {
	if (project.status === 'done') return { percent: 100, stageLabel: 'Завершено' }
	if (project.status === 'failed') return { percent: 0, stageLabel: 'Ошибка' }
	if (!project.current_stage) return { percent: 5, stageLabel: 'Подготовка...' }

	const stageIdx = STAGE_ORDER.indexOf(project.current_stage as StageName)
	if (stageIdx === -1) return { percent: 10, stageLabel: project.current_stage }

	const percent = Math.round(((stageIdx + 1) / STAGE_ORDER.length) * 100)
	const stageLabel = STAGE_NAMES[project.current_stage as StageName] || project.current_stage
	return { percent, stageLabel }
}

export function getStageState(
	project: ProjectRecord | undefined,
	stageKey: StageName,
): ProjectStageStatus {
	if (!project) return 'queued'
	const stageData = project.stages?.[stageKey]
	if (stageData) return stageData.status
	if (project.current_stage === stageKey) return project.status === 'failed' ? 'failed' : 'running'
	if (project.status === 'done') return 'done'
	return 'queued'
}
