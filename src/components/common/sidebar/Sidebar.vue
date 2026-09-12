<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Icon } from '@/components/ui'
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
	<aside
		class="w-48 shrink-0 h-full flex flex-col p-3 select-none"
		style="background: var(--bg-primary)"
	>
		<nav class="flex flex-col gap-1 w-full pt-4">
			<!-- Очередь -->
			<button
				type="button"
				@click="navigateTo('queue')"
				class="w-full flex items-center justify-between px-3 py-2 rounded-xl border-none cursor-pointer transition-all text-xs text-left"
				:class="
					currentRoute === 'queue' || currentRoute === 'new'
						? 'bg-white text-[#0f0f0f] font-semibold'
						: 'bg-transparent text-[var(--text-secondary)] hover:text-white hover:bg-white/5 font-medium'
				"
			>
				<div class="flex items-center gap-3 min-w-0">
					<Icon
						name="list"
						class="w-4 h-4 shrink-0 transition-colors"
						:class="
							currentRoute === 'queue' || currentRoute === 'new' ? 'text-black' : 'text-white'
						"
					/>
					<span class="truncate">Очередь</span>
				</div>

				<span
					v-if="store.queueCount > 0"
					class="text-[10px] font-mono px-1.5 py-0.2 rounded-full font-bold ml-1 shrink-0"
					:class="
						currentRoute === 'queue' || currentRoute === 'new'
							? 'bg-black/15 text-[#0f0f0f]'
							: 'bg-white/10 text-white'
					"
				>
					{{ store.queueCount }}
				</span>
			</button>

			<!-- Контент -->
			<button
				type="button"
				@click="navigateTo('history')"
				class="w-full flex items-center justify-between px-3 py-2 rounded-xl border-none cursor-pointer transition-all text-xs text-left"
				:class="
					currentRoute === 'history'
						? 'bg-white text-[#0f0f0f] font-semibold'
						: 'bg-transparent text-[var(--text-secondary)] hover:text-white hover:bg-white/5 font-medium'
				"
			>
				<div class="flex items-center gap-3 min-w-0">
					<Icon
						name="video"
						class="w-4 h-4 shrink-0 transition-colors"
						:class="currentRoute === 'history' ? 'text-black' : 'text-white'"
					/>
					<span class="truncate">Контент</span>
				</div>

				<span
					v-if="store.historyCount > 0"
					class="text-[10px] font-mono px-1.5 py-0.2 rounded-full font-bold ml-1 shrink-0"
					:class="
						currentRoute === 'history'
							? 'bg-black/15 text-[#0f0f0f]'
							: 'bg-white/10 text-[var(--text-secondary)]'
					"
				>
					{{ store.historyCount }}
				</span>
			</button>
		</nav>
	</aside>
</template>
