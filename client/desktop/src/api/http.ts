/**
 * Minimal typed HTTP client used by feature modules that talk to local
 * services (Python worker, NestJS gateway) over a plain URL.
 */
export async function fetchJson<T>(
	url: string,
	init: RequestInit = {},
	timeoutMs = 8000,
): Promise<T> {
	const controller = new AbortController()
	const timer = setTimeout(() => controller.abort(), timeoutMs)
	try {
		const res = await fetch(url, { ...init, signal: controller.signal })
		if (!res.ok) {
			throw new Error(`HTTP ${res.status} ${res.statusText}`)
		}
		return (await res.json()) as T
	} finally {
		clearTimeout(timer)
	}
}
