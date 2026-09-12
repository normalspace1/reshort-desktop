import { invoke as tauriInvoke } from '@tauri-apps/api/core'

/**
 * Typed wrapper over the Tauri IPC bridge.
 *
 * Feature modules must call commands through this narrow boundary instead of
 * importing `@tauri-apps/api` directly, so all command wiring stays in one place.
 */
export function invoke<T>(command: string, args: Record<string, unknown> = {}): Promise<T> {
	return tauriInvoke<T>(command, args)
}
