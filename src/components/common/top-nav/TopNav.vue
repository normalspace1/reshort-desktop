<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useProjectStore } from '@/stores/project'

const route = useRoute()
const router = useRouter()
const store = useProjectStore()

const currentRoute = computed(() => route.name)

function navigateTo(name: string) {
	router.push({ name })
}
</script>

<template>
	<header
		class="w-full h-14 flex items-center justify-center px-6 shrink-0 select-none"
		style="background: var(--bg-primary)"
	>
		<!-- macOS-style Centered Segmented Navigation -->
		<div class="flex items-center p-0.5 rounded-xl text-xs" style="background: var(--bg-secondary)">
			<!-- Queue -->
			<button
				type="button"
				@click="navigateTo('queue')"
				class="flex items-center gap-1.5 px-4 py-1.5 rounded-lg font-medium border-none cursor-pointer transition-colors"
				:class="
					currentRoute === 'queue' || currentRoute === 'new'
						? 'bg-[var(--bg-tertiary)] text-white'
						: 'bg-transparent text-[var(--text-muted)] hover:text-white'
				"
			>
				<span>Очередь</span>
				<span
					v-if="store.queueCount > 0"
					class="text-[10px] font-mono px-1.5 py-0.2 rounded bg-[var(--accent-subtle)] text-[var(--accent)] font-semibold ml-0.5"
				>
					{{ store.queueCount }}
				</span>
			</button>

			<!-- History -->
			<button
				type="button"
				@click="navigateTo('history')"
				class="flex items-center gap-1.5 px-4 py-1.5 rounded-lg font-medium border-none cursor-pointer transition-colors"
				:class="
					currentRoute === 'history'
						? 'bg-[var(--bg-tertiary)] text-white'
						: 'bg-transparent text-[var(--text-muted)] hover:text-white'
				"
			>
				<span>История</span>
				<span
					v-if="store.historyCount > 0"
					class="text-[10px] font-mono text-[var(--text-muted)] ml-0.5"
				>
					{{ store.historyCount }}
				</span>
			</button>
		</div>
	</header>
</template>
