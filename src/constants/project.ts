import type { ProjectStatusName, StageName } from '@/types/project'

export interface PipelineStageInfo {
	id: StageName
	step: string
	title: string
	description: string
}

export const PIPELINE_STAGES: PipelineStageInfo[] = [
	{
		id: 'download',
		step: '01',
		title: 'Загрузка медиа',
		description: 'Получение потока высокого качества',
	},
	{
		id: 'separate',
		step: '02',
		title: 'Разделение вокала',
		description: 'Изоляция голоса от музыки и эффектов (Demucs)',
	},
	{
		id: 'transcribe',
		step: '03',
		title: 'Распознавание речи',
		description: 'Пословные тайминги (Whisper)',
	},
	{
		id: 'translate',
		step: '04',
		title: 'Перевод и адаптация',
		description: 'Адаптация ритмики под хронометраж',
	},
	{
		id: 'tts',
		step: '05',
		title: 'Клонирование голоса',
		description: 'Zero-shot клонирование тембра (Fish Audio)',
	},
	{
		id: 'mix',
		step: '06',
		title: 'Сведение звука',
		description: 'Динамический дакинг фонового звука',
	},
	{
		id: 'finalize',
		step: '07',
		title: 'Финальный рендер',
		description: 'Сборка и экспорт MP4',
	},
]

export const STAGE_ORDER: StageName[] = [
	'download',
	'separate',
	'transcribe',
	'translate',
	'tts',
	'mix',
	'finalize',
]

export const STAGE_NAMES: Record<StageName, string> = {
	download: 'Загрузка',
	separate: 'Разделение вокала',
	transcribe: 'Транскрипция',
	translate: 'Перевод',
	tts: 'Клонирование голоса',
	mix: 'Сведение звука',
	finalize: 'Рендеринг',
}

export const STATUS_LABELS: Record<ProjectStatusName, string> = {
	queued: 'В очереди',
	running: 'Обработка',
	done: 'Готово',
	failed: 'Ошибка',
	cancelled: 'Отменено',
	paused: 'Пауза',
}
