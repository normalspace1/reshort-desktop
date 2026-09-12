import { onUnmounted } from 'vue'

import { setupApi, type SetupSnapshot } from '@/api/setup'
import { PREFLIGHT_ERRORS, PREFLIGHT_LABELS } from '@/constants/setup'
import { useSetupStore } from '@/stores/setup'
import type { PreflightCheck } from '@/types/setup'

function mapItems(raw: Array<{ id: string; ok: boolean; detail: string }>): PreflightCheck[] {
	return raw.map((i) => ({
		...i,
		label: PREFLIGHT_LABELS[i.id] ?? i.id,
		detail: i.ok ? i.detail : (PREFLIGHT_ERRORS[i.detail] ?? i.detail),
	}))
}

export function useSetup() {
	const store = useSetupStore()
	let pollTimer: ReturnType<typeof setInterval> | null = null
	let lastRunning = false

	function applySnapshot(s: SetupSnapshot) {
		if (s.running) {
			store.installing = true
			store.progress = {
				item: s.item,
				status: s.status,
				done: s.done,
				total: s.total ?? undefined,
			}
		}
	}

	async function check() {
		store.loading = true
		store.error = null
		try {
			const raw = await setupApi.check()
			store.items = mapItems(raw)
		} catch (e) {
			console.error('preflight_check:', e)
			store.error = String(e)
		} finally {
			store.loading = false
		}
	}

	async function tick() {
		let running = false
		try {
			const s = await setupApi.progress()
			running = s.running
			if (running) applySnapshot(s)
		} catch {}

		if (running) {
			lastRunning = true
			return
		}

		const wasRunning = lastRunning
		lastRunning = false
		if (wasRunning || store.items.length === 0) {
			store.installing = false
			store.progress = null
			if (!store.loading) {
				await check()
			}
		}
	}

	function startPoll() {
		if (pollTimer) return
		pollTimer = setInterval(() => tick(), 250)
	}

	function retry() {
		store.error = null
		setupApi
			.retry()
			.then(() => tick())
			.catch((e) => {
				console.error('preflight_retry:', e)
				store.error = String(e)
				check()
			})
	}

	async function init() {
		await tick()
		startPoll()
	}

	onUnmounted(() => {
		if (pollTimer) clearInterval(pollTimer)
	})

	return { check, init, retry }
}
