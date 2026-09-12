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

function formatDuration(seconds?: number): string {
	if (!seconds || seconds <= 0) return ''
	const m = Math.floor(seconds / 60)
	const s = Math.floor(seconds % 60)
	return `${m}:${s < 10 ? '0' : ''}${s}`
}

function formatDate(dateStr?: string): string {
	if (!dateStr) return '—'
	try {
		const d = new Date(dateStr)
		if (isNaN(d.getTime())) return dateStr
		return new Intl.DateTimeFormat('ru-RU', {
			day: 'numeric',
			month: 'short',
			year: 'numeric',
		}).format(d)
	} catch {
		return dateStr
	}
}

async function handleDelete(id: string, e: Event) {
	e.stopPropagation()
	if (confirm('Удалить видео и связанные файлы?')) {
		try {
			await store.deleteProject(id)
			toast.success('Видео удалено')
		} catch (err) {
			toast.error('Не удалось удалить видео')
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
	<div class="w-full flex-1 flex flex-col max-w-5xl mx-auto gap-5 pt-2 pb-12 select-none px-4">
		<!-- Верхняя строка управления: Поиск и Фильтры-пилюли в стиле YouTube Studio -->
		<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
			<!-- Поле поиска -->
			<div class="relative w-full sm:w-72">
				<Icon
					name="search"
					class="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-white pointer-events-none"
				/>
				<Input
					v-model="searchQuery"
					placeholder="Поиск по контенту..."
					class="pl-10 h-9 rounded-full bg-[var(--bg-secondary)] border-none text-xs placeholder:text-[var(--text-muted)]"
				/>
			</div>

			<!-- Фильтры-чипсы (YouTube Studio Filter Chips) -->
			<div class="flex items-center gap-1.5 text-xs overflow-x-auto pb-1 sm:pb-0">
				<button
					type="button"
					@click="selectedFilter = 'all'"
					class="px-3.5 py-1.5 rounded-full border-none cursor-pointer text-xs font-medium transition-all shrink-0"
					:class="
						selectedFilter === 'all'
							? 'bg-white text-[#0f0f0f]'
							: 'bg-white/10 text-[var(--text-secondary)] hover:text-white hover:bg-white/15'
					"
				>
					Все видео
				</button>
				<button
					type="button"
					@click="selectedFilter = 'done'"
					class="px-3.5 py-1.5 rounded-full border-none cursor-pointer text-xs font-medium transition-all shrink-0"
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
					class="px-3.5 py-1.5 rounded-full border-none cursor-pointer text-xs font-medium transition-all shrink-0"
					:class="
						selectedFilter === 'failed'
							? 'bg-white text-[#0f0f0f]'
							: 'bg-white/10 text-[var(--text-secondary)] hover:text-white hover:bg-white/15'
					"
				>
					С ошибками
				</button>
			</div>
		</div>

		<!-- Список видео в формате таблицы YouTube Studio Content List -->
		<div v-if="completedProjects.length > 0" class="flex flex-col w-full">
			<!-- Заголовки колонок -->
			<div
				class="grid grid-cols-12 items-center px-4 py-2 text-[11px] font-medium text-[var(--text-muted)] border-none"
			>
				<div class="col-span-7 sm:col-span-6">Видео</div>
				<div class="col-span-3 sm:col-span-3">Статус</div>
				<div class="hidden sm:block sm:col-span-2">Дата</div>
				<div class="col-span-2 sm:col-span-1 text-right">Действия</div>
			</div>

			<!-- Строки видео -->
			<div class="flex flex-col gap-1 w-full">
				<div
					v-for="p in completedProjects"
					:key="p.id"
					@click="
						p.status === 'done'
							? router.push({ name: 'result', params: { id: p.id } })
							: router.push({ name: 'processing', params: { id: p.id } })
					"
					class="grid grid-cols-12 items-center px-3.5 py-2.5 rounded-2xl cursor-pointer transition-colors hover:bg-[var(--bg-secondary)] group"
				>
					<!-- Колонка видео (Превью + Название + Метаданные) -->
					<div class="col-span-7 sm:col-span-6 flex items-center gap-3.5 min-w-0 pr-3">
						<!-- Превью ролика -->
						<div
							class="w-24 sm:w-28 aspect-video rounded-xl overflow-hidden shrink-0 relative flex items-center justify-center bg-white/5"
						>
							<img
								v-if="p.info?.thumbnail"
								:src="p.info.thumbnail"
								class="w-full h-full object-cover transition-transform group-hover:scale-105"
							/>
							<Icon v-else name="video" class="w-5 h-5 text-white" />

							<!-- Бейдж таймкода в правом нижнем углу (как на YouTube) -->
							<span
								v-if="p.info?.duration"
								class="absolute bottom-1 right-1 bg-black/85 text-white font-mono text-[10px] px-1.5 py-0.2 rounded font-medium"
							>
								{{ formatDuration(p.info.duration) }}
							</span>

							<!-- Оверлей кнопки воспроизведения при наведении на строку -->
							<div
								v-if="p.status === 'done'"
								class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity"
							>
								<Icon name="play" class="w-5 h-5 text-white" />
							</div>
						</div>

						<!-- Заголовок и детали -->
						<div class="flex flex-col min-w-0">
							<span
								class="text-xs font-medium text-white truncate group-hover:text-white"
								:title="p.info?.title || p.id"
							>
								{{ p.info?.title || p.id }}
							</span>
							<div
								class="flex items-center gap-2 text-[11px] text-[var(--text-secondary)] mt-1 truncate"
							>
								<span v-if="p.info?.author" class="truncate">{{ p.info.author }}</span>
								<span
									v-if="p.info?.resolution"
									class="font-mono text-[10px] px-1 rounded bg-white/5"
								>
									{{ p.info.resolution }}
								</span>
								<span v-else class="font-mono text-[10px] truncate">{{ p.id }}</span>
							</div>
						</div>
					</div>

					<!-- Колонка статуса -->
					<div class="col-span-3 sm:col-span-3 flex items-center text-xs">
						<span
							class="inline-flex items-center gap-1.5"
							:class="p.status === 'done' ? 'text-white' : 'text-red-400'"
						>
							<span
								class="w-1.5 h-1.5 rounded-full"
								:class="p.status === 'done' ? 'bg-white' : 'bg-red-400'"
							/>
							<span>{{ p.status === 'done' ? 'Готово' : 'Ошибка' }}</span>
						</span>
					</div>

					<!-- Колонка даты создания -->
					<div class="hidden sm:block sm:col-span-2 text-xs text-[var(--text-secondary)] truncate">
						{{ formatDate(p.created_at) }}
					</div>

					<!-- Колонка действий (появляется при наведении) -->
					<div
						class="col-span-2 sm:col-span-1 flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity"
					>
						<button
							type="button"
							@click="handleOpenFolder(p.id, $event)"
							class="p-1.5 rounded-full text-white hover:bg-white/15 bg-transparent border-none cursor-pointer transition-colors"
							title="Показать в проводнике"
						>
							<Icon name="folder" class="w-3.5 h-3.5 text-white" />
						</button>
						<button
							type="button"
							@click="handleDelete(p.id, $event)"
							class="p-1.5 rounded-full text-white hover:bg-white/15 bg-transparent border-none cursor-pointer transition-colors"
							title="Удалить"
						>
							<Icon name="delete" class="w-3.5 h-3.5 text-white" />
						</button>
					</div>
				</div>
			</div>
		</div>

		<!-- Пустое состояние -->
		<EmptyState
			v-else
			icon="video"
			title="Контент пока пуст"
			:description="
				searchQuery
					? 'Ничего не найдено по вашему запросу'
					: 'Здесь будут отображаться готовые переведенные видео'
			"
		>
			<template #action v-if="!searchQuery">
				<Button size="sm" @click="router.push({ name: 'queue' })"> Перейти в очередь </Button>
			</template>
		</EmptyState>
	</div>
</template>
