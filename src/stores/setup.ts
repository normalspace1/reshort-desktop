import { computed, shallowRef } from 'vue'
import { defineStore } from 'pinia'

import type { SetupProgress } from '@/api/setup'
import { PREFLIGHT_LABELS } from '@/constants/setup'
import type { PreflightCheck } from '@/types/setup'
import { formatBytes } from '@/utils/format'

export const useSetupStore = defineStore('setup', () => {
	const items = shallowRef<PreflightCheck[]>([])
	const loading = shallowRef(false)
	const installing = shallowRef(false)
	const error = shallowRef<string | null>(null)
	const progress = shallowRef<SetupProgress | null>(null)

	const allReady = computed(() => items.value.length > 0 && items.value.every((i) => i.ok))

	const percent = computed(() => {
		const p = progress.value
		if (!p || !p.total) return null
		return Math.round(((p.done ?? 0) / p.total) * 100)
	})

	const progressText = computed(() => {
		const p = progress.value
		if (!p) return ''
		const label = (PREFLIGHT_LABELS[p.item] ?? p.item).toLowerCase()
		if (p.status === 'downloading' && p.total) {
			return `Скачиваем ${label}: ${formatBytes(p.done ?? 0)} из ${formatBytes(p.total)}`
		}
		if (p.status === 'downloading') {
			return `Скачиваем ${label}: ${formatBytes(p.done ?? 0)}`
		}
		if (p.status === 'extracting') {
			return `Распаковываем ${label}…`
		}
		return `Устанавливаем ${label}…`
	})

	return {
		items,
		loading,
		installing,
		error,
		progress,
		allReady,
		percent,
		progressText,
	}
})
