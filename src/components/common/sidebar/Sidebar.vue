<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Icon } from '@/components/ui'

const route = useRoute()
const router = useRouter()

const currentRoute = computed(() => route.name)

const isCollapsed = ref(localStorage.getItem('sidebar_collapsed') === 'true')

function toggleSidebar() {
	isCollapsed.value = !isCollapsed.value
	localStorage.setItem('sidebar_collapsed', String(isCollapsed.value))
}

function navigateTo(name: string) {
	router.push({ name })
}
</script>

<template>
	<aside
		class="shrink-0 h-full flex flex-col p-2 select-none transition-all duration-200"
		:class="isCollapsed ? 'w-16' : 'w-48'"
		style="background: var(--bg-primary)"
	>
		<!-- Кнопка Гамбургера (YouTube Studio style) -->
		<div class="flex items-center h-10 px-1 mb-2">
			<button
				type="button"
				@click="toggleSidebar"
				class="p-2 rounded-full hover:bg-white/10 text-white bg-transparent border-none cursor-pointer transition-colors flex items-center justify-center shrink-0 active:scale-95"
				:title="isCollapsed ? 'Развернуть меню' : 'Свернуть меню'"
			>
				<Icon name="menu" class="w-5 h-5 text-white" />
			</button>
		</div>

		<!-- Список навигации -->
		<nav class="flex flex-col gap-1 w-full">
			<!-- Главная -->
			<button
				type="button"
				@click="navigateTo('queue')"
				class="w-full flex items-center gap-3 rounded-xl border-none cursor-pointer transition-all text-xs text-left active:scale-[0.98]"
				:class="[
					isCollapsed ? 'justify-center p-2.5' : 'justify-start px-3 py-2.5',
					currentRoute === 'queue' || currentRoute === 'new'
						? 'bg-white text-[#0f0f0f] font-semibold'
						: 'bg-transparent text-[var(--text-secondary)] hover:text-white hover:bg-white/5 font-medium',
				]"
				:title="isCollapsed ? 'Главная' : undefined"
			>
				<Icon
					name="home"
					class="w-4 h-4 shrink-0 transition-colors"
					:class="currentRoute === 'queue' || currentRoute === 'new' ? 'text-black' : 'text-white'"
				/>
				<span v-if="!isCollapsed" class="truncate">Главная</span>
			</button>

			<!-- Контент -->
			<button
				type="button"
				@click="navigateTo('history')"
				class="w-full flex items-center gap-3 rounded-xl border-none cursor-pointer transition-all text-xs text-left active:scale-[0.98]"
				:class="[
					isCollapsed ? 'justify-center p-2.5' : 'justify-start px-3 py-2.5',
					currentRoute === 'history'
						? 'bg-white text-[#0f0f0f] font-semibold'
						: 'bg-transparent text-[var(--text-secondary)] hover:text-white hover:bg-white/5 font-medium',
				]"
				:title="isCollapsed ? 'Контент' : undefined"
			>
				<Icon
					name="video"
					class="w-4 h-4 shrink-0 transition-colors"
					:class="currentRoute === 'history' ? 'text-black' : 'text-white'"
				/>
				<span v-if="!isCollapsed" class="truncate">Контент</span>
			</button>
		</nav>
	</aside>
</template>
