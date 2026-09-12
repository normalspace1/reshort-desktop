<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { toast } from 'vue-sonner'
import { projectsApi } from '@/api/projects'
import { EmptyState, VideoThumbnail } from '@/components/common'
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

const pageSize = ref(50)

const displayedProjects = computed(() => completedProjects.value.slice(0, pageSize.value))

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

const deletingId = ref<string | null>(null)

function handleDeleteClick(id: string, e: Event) {
	e.stopPropagation()
	deletingId.value = id
}

async function confirmDelete(id: string, e: Event) {
	e.stopPropagation()
	deletingId.value = null
	try {
		await store.deleteProject(id)
		toast.success('Видео удалено')
	} catch (err) {
		toast.error('Не удалось удалить видео')
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
	<div class="w-full flex-1 flex flex-col max-w-4xl mx-auto gap-6 select-none">
		<!-- Унифицированный заголовок страницы -->
		<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
			<div>
				<h1 class="text-base font-semibold text-white tracking-tight m-0">Контент</h1>
				<p class="text-xs text-[var(--text-secondary)] mt-0.5 m-0">
					Все переведенные видео ({{ completedProjects.length }})
				</p>
			</div>

			<!-- Поиск и Фильтры-пилюли в стиле YouTube Studio -->
			<div class="flex items-center gap-2.5">
				<!-- Поле поиска -->
				<div class="relative w-44 sm:w-52">
					<Icon
						name="search"
						class="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-white pointer-events-none opacity-60"
					/>
					<Input
						v-model="searchQuery"
						placeholder="Поиск..."
						class="pl-8.5 h-8 rounded-full bg-white/5 border-none text-xs placeholder:text-[var(--text-muted)] text-white focus-visible:ring-0"
					/>
				</div>

				<!-- Фильтры-чипсы (YouTube Studio Filter Chips) -->
				<div class="flex items-center gap-1.5 text-xs">
					<button
						type="button"
						@click="selectedFilter = 'all'"
						class="px-3 py-1 rounded-full border-none cursor-pointer text-xs font-medium transition-all shrink-0"
						:class="
							selectedFilter === 'all'
								? 'bg-white text-[#0f0f0f]'
								: 'bg-white/5 text-[var(--text-secondary)] hover:text-white hover:bg-white/10'
						"
					>
						Все
					</button>
					<button
						type="button"
						@click="selectedFilter = 'done'"
						class="px-3 py-1 rounded-full border-none cursor-pointer text-xs font-medium transition-all shrink-0"
						:class="
							selectedFilter === 'done'
								? 'bg-white text-[#0f0f0f]'
								: 'bg-white/5 text-[var(--text-secondary)] hover:text-white hover:bg-white/10'
						"
					>
						Готовые
					</button>
					<button
						type="button"
						@click="selectedFilter = 'failed'"
						class="px-3 py-1 rounded-full border-none cursor-pointer text-xs font-medium transition-all shrink-0"
						:class="
							selectedFilter === 'failed'
								? 'bg-white text-[#0f0f0f]'
								: 'bg-white/5 text-[var(--text-secondary)] hover:text-white hover:bg-white/10'
						"
					>
						Ошибки
					</button>
				</div>
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
					v-for="p in displayedProjects"
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
						<!-- Reusable VideoThumbnail -->
						<VideoThumbnail
							:src="p.info?.thumbnail"
							:duration="p.info?.duration"
							:resolution="p.info?.resolution"
							:show-play-on-hover="p.status === 'done'"
							class="h-16"
						/>

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

					<!-- Колонка статуса (без лишних точек) -->
					<div class="col-span-3 sm:col-span-3 flex items-center text-xs">
						<span :class="p.status === 'done' ? 'text-white' : 'text-red-400'">
							{{ p.status === 'done' ? 'Готово' : 'Ошибка' }}
						</span>
					</div>

					<!-- Колонка даты создания -->
					<div class="hidden sm:block sm:col-span-2 text-xs text-[var(--text-secondary)] truncate">
						{{ formatDate(p.created_at) }}
					</div>

					<!-- Колонка действий (появляется при наведении или при подтверждении удаления) -->
					<div
						class="col-span-2 sm:col-span-1 flex items-center justify-end gap-1 transition-opacity"
						:class="deletingId === p.id ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'"
					>
						<template v-if="deletingId === p.id">
							<button
								type="button"
								@click="confirmDelete(p.id, $event)"
								class="px-2 py-0.5 rounded-full bg-red-500/20 text-red-400 hover:bg-red-500/30 text-[11px] font-medium border-none cursor-pointer transition-colors"
								title="Подтвердить удаление"
							>
								Да
							</button>
							<button
								type="button"
								@click.stop="deletingId = null"
								class="px-2 py-0.5 rounded-full bg-white/10 text-[var(--text-secondary)] hover:text-white text-[11px] font-medium border-none cursor-pointer transition-colors"
								title="Отмена"
							>
								Нет
							</button>
						</template>
						<template v-else>
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
								@click="handleDeleteClick(p.id, $event)"
								class="p-1.5 rounded-full text-white hover:bg-white/15 bg-transparent border-none cursor-pointer transition-colors"
								title="Удалить"
							>
								<Icon name="delete" class="w-3.5 h-3.5 text-white" />
							</button>
						</template>
					</div>
				</div>
			</div>

			<!-- Кнопка пагинации/подгрузки при большом объеме -->
			<div v-if="completedProjects.length > pageSize" class="flex justify-center pt-3 pb-4">
				<button
					type="button"
					@click="pageSize += 50"
					class="px-4 py-2 rounded-full bg-white/5 hover:bg-white/10 text-white text-xs font-medium border-none cursor-pointer transition-colors active:scale-[0.98]"
				>
					Показать еще 50 (осталось {{ completedProjects.length - pageSize }})
				</button>
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
				<Button size="sm" @click="router.push({ name: 'queue' })"> Перейти на главную </Button>
			</template>
		</EmptyState>
	</div>
</template>
