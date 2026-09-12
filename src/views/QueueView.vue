<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { toast } from 'vue-sonner'

import { filePickerApi, generationApi } from '@/api/projects'
import { Button, Icon, Kbd, Switch } from '@/components/ui'
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

// Pipeline parameters
const speed = ref(1.12)
const keepMemes = ref(true)
const burnSubtitles = ref(false)
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
				ttsBaseSpeed: speed.value,
				burnSubtitles: burnSubtitles.value,
				keepMemes: keepMemes.value,
				uniquify: uniquify.value,
				adaptTts: true,
			})
			resetSource()
			await store.loadProjects()
			router.push({ name: 'processing', params: { id: res.project_id } })
		} else if (source.value?.type === 'folder' && source.value.files?.length) {
			const res = await generationApi.startBatch({
				filePaths: source.value.files,
				ttsBaseSpeed: speed.value,
				burnSubtitles: burnSubtitles.value,
				keepMemes: keepMemes.value,
				uniquify: uniquify.value,
				adaptTts: true,
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
				ttsBaseSpeed: speed.value,
				burnSubtitles: burnSubtitles.value,
				keepMemes: keepMemes.value,
				uniquify: uniquify.value,
				adaptTts: true,
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

const recentDoneTasks = computed(() =>
	store.projects.filter((p) => p.status === 'done').slice(0, 4),
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
	<div class="w-full flex-1 flex flex-col max-w-4xl mx-auto gap-6 pt-2 pb-8 select-none">
		<!-- 1. Рабочая станция импорта и параметров -->
		<div
			class="w-full rounded-xl flex flex-col overflow-hidden transition-all"
			style="background: var(--bg-secondary)"
		>
			<!-- Верхняя строка импорта -->
			<div class="flex items-center gap-3 px-4 py-3">
				<!-- Режим выбранного файла / папки -->
				<div
					v-if="source"
					class="flex items-center gap-2.5 px-3 py-1.5 rounded-lg text-xs flex-1 min-w-0"
					style="background: var(--bg-tertiary)"
				>
					<Icon
						:name="source.type === 'folder' ? 'folder' : 'video'"
						class="w-4 h-4 text-white shrink-0"
					/>
					<span class="font-medium truncate text-white">{{ source.name }}</span>
					<span
						v-if="source.count"
						class="text-[11px] px-1.5 py-0.5 rounded text-white"
						style="background: rgba(255, 255, 255, 0.1)"
					>
						{{ source.count }} файлов
					</span>
					<button
						type="button"
						@click="resetSource"
						class="ml-auto p-1 hover:opacity-80 text-white bg-transparent border-none cursor-pointer"
						title="Сбросить выбор"
					>
						<Icon name="close" class="w-3.5 h-3.5 text-white" />
					</button>
				</div>

				<!-- Поле ввода URL -->
				<div v-else class="flex items-center gap-2 flex-1 min-w-0">
					<Icon name="search" class="w-4 h-4 text-white shrink-0" />
					<input
						ref="inputRef"
						v-model="url"
						type="text"
						placeholder="Вставьте ссылку Shorts, Reels, TikTok или выберите файл на диске..."
						class="w-full bg-transparent border-none outline-none text-xs text-[var(--text-primary)] placeholder-[var(--text-muted)] py-1"
					/>
				</div>

				<!-- Кнопки выбора с диска -->
				<div class="flex items-center gap-1.5 shrink-0 pl-2">
					<button
						type="button"
						@click="handlePickFile"
						class="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs text-white hover:bg-[var(--bg-tertiary)] bg-transparent border-none cursor-pointer transition-colors"
						title="Выбрать файл (⌘O)"
					>
						<Icon name="video" class="w-3.5 h-3.5 text-white" />
						<span>Файл</span>
					</button>
					<button
						type="button"
						@click="handlePickFolder"
						class="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs text-white hover:bg-[var(--bg-tertiary)] bg-transparent border-none cursor-pointer transition-colors"
						title="Выбрать папку (⌘⇧O)"
					>
						<Icon name="folder" class="w-3.5 h-3.5 text-white" />
						<span>Папка</span>
					</button>
				</div>
			</div>

			<!-- Нижняя панель технических параметров пайплайна -->
			<div
				class="flex flex-wrap items-center justify-between gap-4 px-4 py-2.5 text-xs"
				style="background: var(--bg-tertiary)"
			>
				<!-- Левая часть: регуляторы пайплайна -->
				<div class="flex flex-wrap items-center gap-4 text-[var(--text-secondary)]">
					<!-- Скорость речи -->
					<div class="flex items-center gap-1.5">
						<span class="text-[11px] text-[var(--text-muted)]">Темп:</span>
						<div class="flex items-center p-0.5 rounded-lg" style="background: var(--bg-secondary)">
							<button
								v-for="s in [1.0, 1.12, 1.25]"
								:key="s"
								type="button"
								@click="speed = s"
								class="px-2 py-0.5 rounded text-[11px] font-medium border-none cursor-pointer transition-colors"
								:class="
									speed === s
										? 'bg-[var(--bg-tertiary)] text-white'
										: 'bg-transparent text-[var(--text-muted)] hover:text-white'
								"
							>
								{{ s }}x
							</button>
						</div>
					</div>

					<!-- Разделитель -->
					<div class="h-3 w-px bg-white/10 hidden sm:block" />

					<!-- Тумблер: Мемы и звуки -->
					<label class="flex items-center gap-2 cursor-pointer hover:text-white transition-colors">
						<Switch v-model="keepMemes" />
						<span class="text-[11px]">Фоновые звуки</span>
					</label>

					<!-- Тумблер: Субтитры -->
					<label class="flex items-center gap-2 cursor-pointer hover:text-white transition-colors">
						<Switch v-model="burnSubtitles" />
						<span class="text-[11px]">Субтитры</span>
					</label>

					<!-- Тумблер: Уникализация -->
					<label class="flex items-center gap-2 cursor-pointer hover:text-white transition-colors">
						<Switch v-model="uniquify" />
						<span class="text-[11px]">Антидетект</span>
					</label>
				</div>

				<!-- Правая часть: кнопка запуска -->
				<div class="flex items-center gap-2 ml-auto">
					<Button :disabled="!canStart" @click="handleStart" size="sm" class="gap-2">
						<Icon v-if="isSubmitting" name="reload" class="w-3.5 h-3.5 animate-spin text-black" />
						<Icon v-else name="play" class="w-3.5 h-3.5 text-black" />
						<span>{{
							source?.type === 'folder' ? `Перевести ${source.count} видео` : 'Перевести видео'
						}}</span>
						<Kbd class="opacity-70 border-none bg-black/10 text-black">⌘↵</Kbd>
					</Button>
				</div>
			</div>
		</div>

		<!-- 2. Секция задач в обработке (Pipeline Queue) -->
		<div v-if="activeTasks.length > 0" class="flex flex-col gap-2.5">
			<div class="flex items-center justify-between px-1">
				<span class="text-xs font-medium text-[var(--text-secondary)]">
					Очередь обработки ({{ activeTasks.length }})
				</span>
			</div>

			<div class="w-full rounded-xl flex flex-col overflow-hidden gap-1">
				<div
					v-for="task in activeTasks"
					:key="task.id"
					@click="router.push({ name: 'processing', params: { id: task.id } })"
					class="flex items-center justify-between p-3.5 rounded-xl cursor-pointer transition-colors hover:bg-[var(--bg-tertiary)] relative"
					style="background: var(--bg-secondary)"
				>
					<div class="flex items-center gap-3 min-w-0 flex-1">
						<Icon name="video" class="w-5 h-5 text-white shrink-0" />
						<div class="flex flex-col min-w-0">
							<span class="text-xs font-medium text-white truncate">
								{{ task.info?.title || task.id }}
							</span>
							<span class="text-[11px] text-[var(--text-muted)] mt-0.5">
								{{
									task.current_stage
										? STAGE_NAMES[task.current_stage as StageName] || task.current_stage
										: 'Инициализация'
								}}
							</span>
						</div>
					</div>

					<div class="flex items-center gap-4 shrink-0 ml-4">
						<div class="w-28 flex flex-col gap-1 items-end">
							<span class="text-xs text-[var(--text-secondary)] font-medium">
								{{ getStageProgress(task) }}%
							</span>
							<div
								class="h-1 w-full rounded-full overflow-hidden"
								style="background: var(--bg-tertiary)"
							>
								<div
									class="h-full transition-all duration-300 rounded-full"
									style="background: var(--accent)"
									:style="{ width: `${getStageProgress(task)}%` }"
								/>
							</div>
						</div>

						<Icon name="arrow-right" class="w-4 h-4 text-white" />
					</div>
				</div>
			</div>
		</div>

		<!-- 3. Недавние готовые результаты (Recent Studio Exports) -->
		<div v-if="recentDoneTasks.length > 0" class="flex flex-col gap-2.5">
			<div class="flex items-center justify-between px-1">
				<span class="text-xs font-medium text-[var(--text-secondary)]">Готовые видео</span>
				<button
					type="button"
					@click="router.push({ name: 'history' })"
					class="text-xs text-[var(--text-muted)] hover:text-white bg-transparent border-none cursor-pointer p-0"
				>
					Вся история →
				</button>
			</div>

			<div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
				<div
					v-for="done in recentDoneTasks"
					:key="done.id"
					@click="router.push({ name: 'result', params: { id: done.id } })"
					class="flex flex-col p-2.5 rounded-xl cursor-pointer transition-all hover:bg-[var(--bg-tertiary)] group"
					style="background: var(--bg-secondary)"
				>
					<div
						class="w-full aspect-[9/16] max-h-36 rounded-lg mb-2 overflow-hidden flex items-center justify-center relative"
						style="background: var(--bg-tertiary)"
					>
						<img
							v-if="done.info?.thumbnail"
							:src="done.info.thumbnail"
							class="w-full h-full object-cover transition-transform group-hover:scale-105"
						/>
						<Icon v-else name="video" class="w-6 h-6 text-white" />
						<div
							class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity"
						>
							<Icon name="play" class="w-8 h-8 text-white drop-shadow-md" />
						</div>
					</div>
					<span class="text-xs text-white truncate font-medium">
						{{ done.info?.title || done.id }}
					</span>
				</div>
			</div>
		</div>
	</div>
</template>
