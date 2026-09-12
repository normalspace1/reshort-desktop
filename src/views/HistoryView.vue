<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { toast } from 'vue-sonner'
import { projectsApi } from '@/api/projects'
import { EmptyState } from '@/components/common'
import { Button, Icon, Input } from '@/components/ui'
import { useProjectStore } from '@/stores/project'

const router = useRouter()
const store = useProjectStore()

const searchQuery = ref('')
const selectedFilter = ref<'all' | 'done' | 'failed'>('all')

const completedProjects = computed(() => {
	let list = store.projects.filter((p) => p.status === 'done' || p.status === 'failed')

	if (selectedFilter.value !== 'all') {
		list = list.filter((p) => p.status === selectedFilter.value)
	}

	if (searchQuery.value.trim()) {
		const q = searchQuery.value.toLowerCase().trim()
		list = list.filter(
			(p) =>
				(p.info?.title && p.info.title.toLowerCase().includes(q)) || p.id.toLowerCase().includes(q),
		)
	}

	return list
})

async function handleDelete(id: string, e: Event) {
	e.stopPropagation()
	if (confirm('Удалить проект и связанные файлы?')) {
		try {
			await store.deleteProject(id)
			toast.success('Проект удален')
		} catch (err) {
			toast.error('Не удалось удалить проект')
		}
	}
}

async function handleOpenFolder(id: string, e: Event) {
	e.stopPropagation()
	try {
		await projectsApi.openFolder(id)
	} catch (err) {
		console.error(err)
	}
}

onMounted(() => {
	store.loadProjects()
})
</script>

<template>
	<div class="w-full flex-1 flex flex-col max-w-4xl mx-auto gap-6 pt-2 pb-8 select-none">
		<!-- Верхняя строка: поиск и фильтры -->
		<div class="flex items-center justify-between gap-3">
			<!-- Поле поиска (Shadcn Input) -->
			<div class="relative w-64">
				<Icon
					name="search"
					class="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-white pointer-events-none"
				/>
				<Input v-model="searchQuery" placeholder="Поиск по названию..." class="pl-9 rounded-full" />
			</div>

			<!-- Фильтры статуса в стиле YouTube Studio Chips -->
			<div class="flex items-center gap-1.5 text-xs">
				<button
					type="button"
					@click="selectedFilter = 'all'"
					class="px-3 py-1 rounded-full border-none cursor-pointer text-xs font-medium transition-all"
					:class="
						selectedFilter === 'all'
							? 'bg-white text-[#0f0f0f]'
							: 'bg-white/10 text-[var(--text-secondary)] hover:text-white hover:bg-white/15'
					"
				>
					Все
				</button>
				<button
					type="button"
					@click="selectedFilter = 'done'"
					class="px-3 py-1 rounded-full border-none cursor-pointer text-xs font-medium transition-all"
					:class="
						selectedFilter === 'done'
							? 'bg-white text-[#0f0f0f]'
							: 'bg-white/10 text-[var(--text-secondary)] hover:text-white hover:bg-white/15'
					"
				>
					Готовые
				</button>
				<button
					type="button"
					@click="selectedFilter = 'failed'"
					class="px-3 py-1 rounded-full border-none cursor-pointer text-xs font-medium transition-all"
					:class="
						selectedFilter === 'failed'
							? 'bg-white text-[#0f0f0f]'
							: 'bg-white/10 text-[var(--text-secondary)] hover:text-white hover:bg-white/15'
					"
				>
					Ошибки
				</button>
			</div>
		</div>

		<!-- Сетка готовых проектов -->
		<div
			v-if="completedProjects.length > 0"
			class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3"
		>
			<div
				v-for="p in completedProjects"
				:key="p.id"
				@click="
					p.status === 'done'
						? router.push({ name: 'result', params: { id: p.id } })
						: router.push({ name: 'processing', params: { id: p.id } })
				"
				class="flex flex-col rounded-xl overflow-hidden cursor-pointer transition-all hover:bg-[var(--bg-tertiary)] group p-2"
				style="background: var(--bg-secondary)"
			>
				<!-- Постер видео -->
				<div
					class="w-full aspect-[9/16] max-h-44 rounded-lg overflow-hidden relative flex items-center justify-center mb-2"
					style="background: var(--bg-tertiary)"
				>
					<img
						v-if="p.info?.thumbnail"
						:src="p.info.thumbnail"
						class="w-full h-full object-cover transition-transform group-hover:scale-105"
					/>
					<Icon v-else name="video" class="w-6 h-6 text-white" />

					<!-- Оверлей воспроизведения при наведении -->
					<div
						v-if="p.status === 'done'"
						class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity"
					>
						<Icon name="play" class="w-6 h-6 text-white" />
					</div>
				</div>

				<!-- Название и кнопки действий -->
				<div class="flex items-center justify-between px-1">
					<span class="text-xs text-white truncate max-w-[120px]" :title="p.info?.title || p.id">
						{{ p.info?.title || p.id }}
					</span>

					<div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
						<button
							type="button"
							@click="handleOpenFolder(p.id, $event)"
							class="p-0.5 text-white hover:opacity-75 bg-transparent border-none cursor-pointer"
							title="Показать в проводнике"
						>
							<Icon name="folder" class="w-3.5 h-3.5 text-white" />
						</button>
						<button
							type="button"
							@click="handleDelete(p.id, $event)"
							class="p-0.5 text-white hover:opacity-75 bg-transparent border-none cursor-pointer"
							title="Удалить"
						>
							<Icon name="delete" class="w-3.5 h-3.5 text-white" />
						</button>
					</div>
				</div>
			</div>
		</div>

		<!-- Пустое состояние (компонент EmptyState) -->
		<EmptyState
			v-else
			icon="video"
			title="История пока пуста"
			:description="
				searchQuery
					? 'Ничего не найдено по вашему запросу'
					: 'Здесь будут появляться переведенные видео'
			"
		>
			<template #action v-if="!searchQuery">
				<Button size="sm" @click="router.push({ name: 'queue' })"> Перейти в очередь </Button>
			</template>
		</EmptyState>
	</div>
</template>
