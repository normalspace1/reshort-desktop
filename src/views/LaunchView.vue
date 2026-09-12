<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import { Icon } from '@/components/ui'

import { setupApi } from '@/api/setup'
import { useSetup } from '@/composables/useSetup'
import { useSetupStore } from '@/stores/setup'

const emit = defineEmits<{ ready: [] }>()

const store = useSetupStore()
const { init, retry } = useSetup()

const remaining = computed(() => store.items.filter((i) => !i.ok))

let proceeded = false

function proceed() {
	if (proceeded) return
	proceeded = true
	emit('ready')
}

function isActive(id: string) {
	return store.installing && store.progress?.item === id
}

const chipStyles = computed(() => {
	const map: Record<string, string> = {}
	for (const i of store.items) {
		if (isActive(i.id)) {
			map[i.id] = 'background: var(--bg-tertiary); color: var(--accent)'
		} else if (i.ok) {
			map[i.id] = 'background: var(--success-bg); color: var(--success)'
		} else {
			map[i.id] = 'background: var(--bg-tertiary); color: var(--text-muted)'
		}
	}
	return map
})

onMounted(async () => {
	setupApi.start().catch(() => {})
	await init()
	if (store.allReady) proceed()
})

watch(
	() => store.allReady,
	(v) => {
		if (v && !store.installing && !store.loading) {
			setTimeout(proceed, 300)
		}
	},
	{ immediate: true },
)
</script>

<template>
	<div class="flex h-full w-full items-center justify-center" style="background: var(--bg-primary)">
		<div class="w-full max-w-[400px] flex flex-col items-center gap-6 px-8">
			<div v-if="store.installing" class="w-full flex flex-col gap-1.5">
				<span class="text-xs" style="color: var(--text-primary)">{{
					store.progressText || 'Загрузка…'
				}}</span>
				<div class="flex items-center gap-3">
					<div
						class="h-1 flex-1 rounded-full overflow-hidden"
						style="background: var(--bg-tertiary)"
					>
						<div
							class="h-full rounded-full transition-all duration-200"
							:style="{ width: (store.percent ?? 0) + '%', background: 'var(--accent)' }"
						/>
					</div>
					<span
						v-if="store.percent !== null"
						class="text-xs shrink-0"
						style="color: var(--text-muted)"
						>{{ store.percent }}%</span
					>
				</div>
				<div v-if="store.error" class="w-full mt-1 text-xs text-center" style="color: var(--error)">
					{{ store.error }}
					<button class="underline cursor-pointer hover:opacity-80" @click="retry">
						Повторить
					</button>
				</div>
			</div>

			<div v-else-if="store.loading" class="flex items-center gap-2 text-white">
				<Icon name="reload" class="w-4 h-4 animate-spin text-white" />
				<span class="text-sm">Проверка…</span>
			</div>

			<template v-else-if="store.items.length">
				<div v-if="remaining.length" class="w-full flex flex-wrap justify-center gap-2">
					<span
						v-for="m in remaining"
						:key="m.id"
						class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium transition-colors"
						:style="chipStyles[m.id]"
					>
						<Icon v-if="isActive(m.id)" name="reload" class="w-3 h-3 animate-spin text-white" />
						<Icon v-else-if="m.ok" name="check" class="w-3 h-3 text-white" />
						<span v-else class="w-1.5 h-1.5 rounded-full" style="background: currentColor" />
						{{ m.label }}
					</span>
				</div>

				<div v-if="store.error" class="w-full text-xs text-center" style="color: var(--error)">
					{{ store.error }}
					<button class="underline cursor-pointer hover:opacity-80" @click="retry">
						Повторить
					</button>
				</div>
			</template>

			<div v-else class="flex flex-col items-center gap-3">
				<div v-if="store.error" class="w-full text-xs text-center" style="color: var(--error)">
					{{ store.error }}
					<button class="underline cursor-pointer hover:opacity-80" @click="retry">
						Повторить
					</button>
				</div>
				<div v-else class="flex items-center gap-2 text-white">
					<Icon name="reload" class="w-4 h-4 animate-spin text-white" />
					<span class="text-sm">Проверка…</span>
				</div>
			</div>
		</div>
	</div>
</template>
