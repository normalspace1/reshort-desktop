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
		<!-- YouTube Studio Style Centered Pill Navigation -->
		<div
			class="flex items-center p-1 rounded-full text-xs gap-1"
			style="background: var(--bg-secondary)"
		>
			<!-- Queue -->
			<button
				type="button"
				@click="navigateTo('queue')"
				class="flex items-center gap-1.5 px-4 py-1.5 rounded-full font-medium border-none cursor-pointer transition-all"
				:class="
					currentRoute === 'queue' || currentRoute === 'new'
						? 'bg-white text-[#0f0f0f]'
						: 'bg-transparent text-[var(--text-secondary)] hover:text-white'
				"
			>
				<span>Очередь</span>
				<span
					v-if="store.queueCount > 0"
					class="text-[10px] font-mono px-1.5 py-0.5 rounded-full font-semibold ml-0.5"
					:class="
						currentRoute === 'queue' || currentRoute === 'new'
							? 'bg-black/10 text-[#0f0f0f]'
							: 'bg-white/10 text-white'
					"
				>
					{{ store.queueCount }}
				</span>
			</button>

			<!-- History -->
			<button
				type="button"
				@click="navigateTo('history')"
				class="flex items-center gap-1.5 px-4 py-1.5 rounded-full font-medium border-none cursor-pointer transition-all"
				:class="
					currentRoute === 'history'
						? 'bg-white text-[#0f0f0f]'
						: 'bg-transparent text-[var(--text-secondary)] hover:text-white'
				"
			>
				<span>История</span>
				<span
					v-if="store.historyCount > 0"
					class="text-[10px] font-mono px-1.5 py-0.5 rounded-full ml-0.5"
					:class="
						currentRoute === 'history'
							? 'bg-black/10 text-[#0f0f0f]'
							: 'bg-white/10 text-[var(--text-secondary)]'
					"
				>
					{{ store.historyCount }}
				</span>
			</button>
		</div>
	</header>
</template>
