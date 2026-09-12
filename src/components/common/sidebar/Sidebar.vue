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
		class="w-56 shrink-0 h-full flex flex-col justify-between p-3 select-none border-r border-white/5"
		style="background: var(--bg-primary)"
	>
		<!-- Верхняя часть: Логотип и Навигация -->
		<div class="flex flex-col gap-5">
			<!-- Заголовок приложения в стиле YouTube Studio -->
			<div class="flex items-center gap-2.5 px-3 py-2">
				<div class="w-7 h-7 rounded-xl bg-white/10 flex items-center justify-center shrink-0">
					<Icon name="video" class="w-4 h-4 text-white" />
				</div>
				<div class="flex items-center gap-1.5 min-w-0">
					<span class="text-sm font-semibold tracking-tight text-white">ReShort</span>
					<span
						class="text-[10px] font-mono font-medium px-1.5 py-0.2 rounded bg-white/10 text-[var(--text-secondary)]"
					>
						Studio
					</span>
				</div>
			</div>

			<!-- Список навигации -->
			<nav class="flex flex-col gap-1 w-full">
				<!-- Очередь (Queue) -->
				<button
					type="button"
					@click="navigateTo('queue')"
					class="w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl border-none cursor-pointer transition-all text-xs text-left"
					:class="
						currentRoute === 'queue' || currentRoute === 'new'
							? 'bg-white text-[#0f0f0f] font-semibold shadow-sm'
							: 'bg-transparent text-[var(--text-secondary)] hover:text-white hover:bg-white/5 font-medium'
					"
				>
					<div class="flex items-center gap-3 min-w-0">
						<Icon
							name="list"
							class="w-4 h-4 shrink-0 transition-colors"
							:class="
								currentRoute === 'queue' || currentRoute === 'new'
									? 'text-black'
									: 'text-white opacity-80'
							"
						/>
						<span class="truncate">Очередь</span>
					</div>

					<span
						v-if="store.queueCount > 0"
						class="text-[10px] font-mono px-2 py-0.5 rounded-full font-bold ml-1 shrink-0"
						:class="
							currentRoute === 'queue' || currentRoute === 'new'
								? 'bg-black/15 text-[#0f0f0f]'
								: 'bg-white/10 text-white'
						"
					>
						{{ store.queueCount }}
					</span>
				</button>

				<!-- Контент (History) -->
				<button
					type="button"
					@click="navigateTo('history')"
					class="w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl border-none cursor-pointer transition-all text-xs text-left"
					:class="
						currentRoute === 'history'
							? 'bg-white text-[#0f0f0f] font-semibold shadow-sm'
							: 'bg-transparent text-[var(--text-secondary)] hover:text-white hover:bg-white/5 font-medium'
					"
				>
					<div class="flex items-center gap-3 min-w-0">
						<Icon
							name="video"
							class="w-4 h-4 shrink-0 transition-colors"
							:class="currentRoute === 'history' ? 'text-black' : 'text-white opacity-80'"
						/>
						<span class="truncate">Контент</span>
					</div>

					<span
						v-if="store.historyCount > 0"
						class="text-[10px] font-mono px-2 py-0.5 rounded-full font-bold ml-1 shrink-0"
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
		</div>

		<!-- Нижняя часть: Статус движка и системная панель -->
		<div class="flex flex-col gap-2 pt-3 border-t border-white/5">
			<!-- Быстрый вызов палитры команд (⌘K) -->
			<button
				type="button"
				@click="store.commandPaletteOpen = true"
				class="w-full flex items-center justify-between px-3 py-2 rounded-xl bg-white/5 hover:bg-white/10 border-none cursor-pointer text-xs text-[var(--text-secondary)] hover:text-white transition-colors"
			>
				<div class="flex items-center gap-2">
					<Icon name="search" class="w-3.5 h-3.5 text-white opacity-70" />
					<span class="text-[11px]">Команды</span>
				</div>
				<kbd class="text-[10px] font-mono px-1.5 py-0.5 rounded bg-white/10 text-white/80">⌘K</kbd>
			</button>

			<!-- Статус локального AI движка -->
			<div
				class="flex items-center justify-between px-3 py-1.5 text-[11px] text-[var(--text-muted)]"
			>
				<div class="flex items-center gap-1.5">
					<span class="text-white/80">Локальный AI</span>
					<span>·</span>
					<span class="text-white/60">Активен</span>
				</div>
				<span class="font-mono text-[10px] text-white/50">v0.1</span>
			</div>
		</div>
	</aside>
</template>
