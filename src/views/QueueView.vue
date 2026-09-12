<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { toast } from 'vue-sonner'

import { filePickerApi, generationApi } from '@/api/projects'
import { Button, Icon, Switch } from '@/components/ui'
import { STAGE_NAMES } from '@/constants/project'
import { useProjectStore } from '@/stores/project'
import type { ProjectRecord, StageName } from '@/types/project'
import { validateVideoUrl } from '@/utils/validators'

interface SourceItem {
	type: 'file' | 'folder'
	path: string
	name: string
	count?: number
	files?: string[]
}

const store = useProjectStore()
const router = useRouter()

const url = ref('')
const source = ref<SourceItem | null>(null)
const isSubmitting = ref(false)
const inputRef = ref<HTMLInputElement | null>(null)

const speed = 1.12
const keepMemes = ref(true)
const uniquify = ref(true)

function resetSource() {
	source.value = null
	url.value = ''
}

function getFileName(p: string) {
	return p.split(/[/\\]/).pop() || p
}

async function handlePickFile() {
	try {
		const file = await filePickerApi.pickFile()
		if (file) {
			source.value = {
				type: 'file',
				path: file,
				name: getFileName(file),
			}
		}
	} catch (e) {
		console.error('pickFile:', e)
		toast.error('Не удалось выбрать файл')
	}
}

async function handlePickFolder() {
	try {
		const folder = await filePickerApi.pickFolder()
		if (folder) {
			const videos = await filePickerApi.scanFolder(folder)
			if (videos.length === 0) {
				toast.warning('В выбранной папке нет видеофайлов')
				return
			}
			source.value = {
				type: 'folder',
				path: folder,
				name: getFileName(folder),
				count: videos.length,
				files: videos,
			}
		}
	} catch (e) {
		console.error('pickFolder:', e)
		toast.error('Не удалось выбрать папку')
	}
}

async function handlePaste() {
	try {
		const text = await navigator.clipboard.readText()
		if (text && text.trim()) {
			url.value = text.trim()
			inputRef.value?.focus()
		} else {
			toast.info('Буфер обмена пуст')
		}
	} catch {
		inputRef.value?.focus()
	}
}

const urlValidation = computed(() => {
	if (!url.value || !url.value.trim()) return null
	const res = validateVideoUrl(url.value)
	if (!res.isValid) {
		return 'Поддерживаются ссылки YouTube Shorts, TikTok, Instagram Reels или VK'
	}
	return null
})

const canStart = computed(() => {
	if (isSubmitting.value) return false
	if (source.value) return true
	return validateVideoUrl(url.value).isValid
})

async function handleStart() {
	if (!canStart.value) return
	isSubmitting.value = true

	try {
		if (source.value?.type === 'file') {
			const res = await generationApi.startLocal({
				filePath: source.value.path,
				ttsBaseSpeed: speed,
				burnSubtitles: false,
				keepMemes: keepMemes.value,
				uniquify: uniquify.value,
				adaptTts: false,
			})
			resetSource()
			await store.loadProjects()
			router.push({ name: 'processing', params: { id: res.project_id } })
		} else if (source.value?.type === 'folder' && source.value.files?.length) {
			const res = await generationApi.startBatch({
				filePaths: source.value.files,
				ttsBaseSpeed: speed,
				burnSubtitles: false,
				keepMemes: keepMemes.value,
				uniquify: uniquify.value,
				adaptTts: false,
			})
			resetSource()
			await store.loadProjects()
			if (res.project_ids.length > 0) {
				router.push({ name: 'processing', params: { id: res.project_ids[0] } })
			}
		} else if (url.value) {
			const res = await generationApi.start({
				url: url.value,
				title: 'Короткое видео',
				author: '',
				thumbnail: '',
				ttsBaseSpeed: speed,
				burnSubtitles: false,
				keepMemes: keepMemes.value,
				uniquify: uniquify.value,
				adaptTts: false,
			})
			resetSource()
			await store.loadProjects()
			router.push({ name: 'processing', params: { id: res.project_id } })
		}
	} catch (e: any) {
		console.error('generation start error:', e)
		toast.error(e?.toString() || 'Ошибка запуска')
	} finally {
		isSubmitting.value = false
	}
}

const activeTasks = computed(() =>
	store.projects.filter((p) => p.status === 'running' || p.status === 'queued'),
)

const isQueueExpanded = ref(false)

const visibleActiveTasks = computed(() => {
	if (isQueueExpanded.value) return activeTasks.value
	return activeTasks.value.slice(0, 4)
})

const runningTasksCount = computed(
	() => activeTasks.value.filter((p) => p.status === 'running').length,
)

const queuedTasksCount = computed(
	() => activeTasks.value.filter((p) => p.status === 'queued').length,
)

function getStageProgress(project: ProjectRecord): number {
	const order = ['download', 'separate', 'transcribe', 'translate', 'tts', 'mix', 'finalize']
	if (!project.current_stage) return 8
	const idx = order.indexOf(project.current_stage)
	if (idx === -1) return 15
	return Math.round(((idx + 1) / order.length) * 100)
}

function handleKeyDown(e: KeyboardEvent) {
	if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
		e.preventDefault()
		if (canStart.value) handleStart()
	} else if ((e.metaKey || e.ctrlKey) && e.key === 'o' && !e.shiftKey) {
		e.preventDefault()
		handlePickFile()
	} else if ((e.metaKey || e.ctrlKey) && e.shiftKey && (e.key === 'O' || e.key === 'o')) {
		e.preventDefault()
		handlePickFolder()
	}
}

onMounted(() => {
	inputRef.value?.focus()
	window.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
	window.removeEventListener('keydown', handleKeyDown)
})
</script>

<template>
	<div class="w-full flex-1 flex flex-col max-w-5xl gap-6 select-none">
		<!-- Унифицированный заголовок страницы -->
		<div class="flex items-center justify-between gap-4">
			<div>
				<h1 class="text-base font-semibold text-white tracking-tight m-0">Новый перевод</h1>
				<p class="text-xs text-[var(--text-secondary)] mt-0.5 m-0">
					Дубляж Shorts, Reels, TikTok и локальных видео
				</p>
			</div>
			<div
				v-if="activeTasks.length > 0"
				class="flex items-center gap-2 text-xs text-[var(--text-secondary)]"
			>
				<span
					>В обработке: <strong class="text-white">{{ activeTasks.length }}</strong></span
				>
			</div>
		</div>

		<!-- 1. Рабочая станция перевода -->
		<div
			class="w-full rounded-2xl p-5 flex flex-col gap-4 transition-all"
			style="background: var(--bg-secondary)"
		>
			<!-- Поле ввода ссылки / выбранного источника -->
			<div class="flex items-center gap-3">
				<!-- Выбранный файл или папка -->
				<div
					v-if="source"
					class="flex items-center gap-2.5 px-3.5 py-2 rounded-xl text-xs flex-1 min-w-0 bg-white/5"
				>
					<Icon
						:name="source.type === 'folder' ? 'folder' : 'video'"
						class="w-4 h-4 text-white shrink-0"
					/>
					<span class="font-medium truncate text-white">{{ source.name }}</span>
					<span
						v-if="source.count"
						class="text-[11px] px-2 py-0.5 rounded-full text-white bg-white/10"
					>
						{{ source.count }} файлов
					</span>
					<button
						type="button"
						@click="resetSource"
						class="ml-auto p-1 hover:opacity-75 text-white bg-transparent border-none cursor-pointer"
						title="Сбросить выбор"
					>
						<Icon name="close" class="w-3.5 h-3.5 text-white" />
					</button>
				</div>

				<!-- Ввод ссылки (Shorts / Reels / TikTok) -->
				<div
					v-else
					class="flex items-center gap-2.5 flex-1 min-w-0 px-3.5 py-2 rounded-xl bg-white/5 focus-within:ring-1 focus-within:ring-white/20 transition-all"
				>
					<Icon name="search" class="w-4 h-4 text-white shrink-0 opacity-70" />
					<input
						ref="inputRef"
						v-model="url"
						type="text"
						placeholder="Вставьте ссылку Shorts, Reels, TikTok или выберите файл..."
						class="w-full bg-transparent border-none outline-none text-xs text-white placeholder:text-[var(--text-muted)]"
					/>

					<!-- Быстрая вставка из буфера если поле пустое -->
					<button
						v-if="!url"
						type="button"
						@click="handlePaste"
						class="px-2 py-0.5 rounded-lg text-[11px] font-medium text-[var(--text-secondary)] hover:text-white hover:bg-white/10 bg-transparent border-none cursor-pointer transition-colors shrink-0 flex items-center gap-1 active:scale-[0.97]"
						title="Вставить из буфера (⌘V)"
					>
						<Icon name="copy" class="w-3 h-3 text-white opacity-75" />
						<span>Вставить</span>
					</button>

					<!-- Очистить поле если есть текст -->
					<button
						v-else
						type="button"
						@click="url = ''"
						class="p-0.5 hover:opacity-80 text-white bg-transparent border-none cursor-pointer shrink-0"
						title="Очистить поле"
					>
						<Icon name="close" class="w-3.5 h-3.5 text-white opacity-70" />
					</button>
				</div>

				<!-- Кнопки выбора файлов -->
				<div class="flex items-center gap-1.5 shrink-0">
					<button
						type="button"
						@click="handlePickFile"
						class="flex items-center gap-1.5 px-3.5 py-2 rounded-full text-xs font-medium text-white hover:bg-white/10 bg-white/5 border-none cursor-pointer transition-all active:scale-[0.98]"
						title="Выбрать файл (⌘O)"
					>
						<Icon name="video" class="w-3.5 h-3.5 text-white" />
						<span>Файл</span>
					</button>
					<button
						type="button"
						@click="handlePickFolder"
						class="flex items-center gap-1.5 px-3.5 py-2 rounded-full text-xs font-medium text-white hover:bg-white/10 bg-white/5 border-none cursor-pointer transition-all active:scale-[0.98]"
						title="Выбрать папку (⌘⇧O)"
					>
						<Icon name="folder" class="w-3.5 h-3.5 text-white" />
						<span>Папка</span>
					</button>
				</div>
			</div>

			<!-- Подсказка валидации ссылки -->
			<div
				v-if="urlValidation"
				class="text-[11px] text-[#f87171] -mt-1 px-1 flex items-center gap-1.5"
			>
				<Icon name="info" class="w-3.5 h-3.5 text-[#f87171] shrink-0" />
				<span>{{ urlValidation }}</span>
			</div>

			<!-- Нижняя строка: настройки и запуск -->
			<div class="flex flex-wrap items-center justify-between gap-4 pt-1 text-xs">
				<div class="flex flex-wrap items-center gap-5 text-[var(--text-secondary)]">
					<!-- Тумблеры с расшифровкой -->
					<label
						class="flex items-center gap-2 cursor-pointer hover:text-white transition-colors"
						title="Сохраняет оригинальную музыку, смех и звуковые эффекты под русской речью"
					>
						<Switch v-model="keepMemes" />
						<span class="text-xs">Фоновый звук</span>
					</label>

					<label
						class="flex items-center gap-2 cursor-pointer hover:text-white transition-colors"
						title="Микро-модификация частот звука и кадров для защиты от теневых банов и повторного контента"
					>
						<Switch v-model="uniquify" />
						<span class="text-xs">Антидетект</span>
					</label>
				</div>

				<!-- Кнопка запуска -->
				<div class="ml-auto">
					<Button
						:disabled="!canStart"
						@click="handleStart"
						class="px-5 h-9 font-medium gap-2 active:scale-[0.98] transition-transform"
					>
						<Icon v-if="isSubmitting" name="reload" class="w-4 h-4 animate-spin text-black" />
						<Icon v-else name="play" class="w-4 h-4 text-black" />
						<span>{{
							source?.type === 'folder' ? `Перевести ${source.count} видео` : 'Перевести'
						}}</span>
					</Button>
				</div>
			</div>
		</div>

		<!-- 2. Секция задач в обработке -->
		<div v-if="activeTasks.length > 0" class="flex flex-col gap-2.5">
			<!-- Заголовок очереди с батч-сводкой -->
			<div class="flex items-center justify-between px-1">
				<div class="flex items-center gap-2">
					<span class="text-xs font-medium text-[var(--text-secondary)]">
						Очередь обработки ({{ activeTasks.length }})
					</span>
					<span
						v-if="activeTasks.length > 4"
						class="text-[10px] px-2 py-0.5 rounded-full bg-white/10 text-white font-mono"
					>
						{{ runningTasksCount }} в процессе · {{ queuedTasksCount }} ожидают
					</span>
				</div>

				<button
					v-if="activeTasks.length > 4"
					type="button"
					@click="isQueueExpanded = !isQueueExpanded"
					class="text-xs text-[var(--text-secondary)] hover:text-white bg-transparent border-none cursor-pointer p-0 transition-colors"
				>
					{{ isQueueExpanded ? 'Свернуть ▴' : `Показать все (${activeTasks.length}) ▾` }}
				</button>
			</div>

			<div
				class="w-full flex flex-col gap-2 transition-all"
				:class="{ 'max-h-[480px] overflow-y-auto pr-1': isQueueExpanded }"
			>
				<div
					v-for="task in visibleActiveTasks"
					:key="task.id"
					@click="router.push({ name: 'processing', params: { id: task.id } })"
					class="flex items-center justify-between p-4 rounded-2xl cursor-pointer transition-all hover:bg-[var(--bg-hover)] relative group"
					style="background: var(--bg-secondary)"
				>
					<div class="flex items-center gap-3.5 min-w-0 flex-1">
						<Icon name="video" class="w-5 h-5 text-white shrink-0" />
						<div class="flex flex-col min-w-0">
							<span class="text-xs font-medium text-white truncate">
								{{ task.info?.title || task.id }}
							</span>
							<div class="flex items-center gap-2 mt-0.5">
								<span
									class="text-[11px]"
									:class="
										task.status === 'running'
											? 'text-white font-medium'
											: 'text-[var(--text-secondary)]'
									"
								>
									{{
										task.status === 'running'
											? task.current_stage
												? STAGE_NAMES[task.current_stage as StageName] || task.current_stage
												: 'Обработка...'
											: 'В очереди на дубляж'
									}}
								</span>
								<span
									v-if="task.status === 'running'"
									class="text-[10px] px-1.5 py-0.2 rounded-full bg-white/10 text-white font-mono"
								>
									Активно
								</span>
							</div>
						</div>
					</div>

					<div class="flex items-center gap-4 shrink-0 ml-4">
						<div class="w-28 flex flex-col gap-1 items-end">
							<span class="text-xs text-white font-mono font-medium">
								{{ task.status === 'running' ? `${getStageProgress(task)}%` : 'В очереди' }}
							</span>
							<div class="h-1 w-full rounded-full overflow-hidden bg-white/10">
								<div
									class="h-full transition-all duration-300 rounded-full bg-white"
									:style="{
										width: task.status === 'running' ? `${getStageProgress(task)}%` : '0%',
									}"
								/>
							</div>
						</div>

						<Icon
							name="arrow-right"
							class="w-4 h-4 text-white opacity-70 group-hover:opacity-100 transition-opacity"
						/>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>
