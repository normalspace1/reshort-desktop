<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { toast } from 'vue-sonner'

import { filePickerApi, generationApi } from '@/api/projects'
import { Button, Icon, Kbd } from '@/components/ui'
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

// Minimalist parameters
const speed = ref(1.12)
const keepMemes = ref(true)

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
				burnSubtitles: false,
				keepMemes: keepMemes.value,
				uniquify: true,
				adaptTts: true,
			})
			resetSource()
			await store.loadProjects()
			router.push({ name: 'processing', params: { id: res.project_id } })
		} else if (source.value?.type === 'folder' && source.value.files?.length) {
			const res = await generationApi.startBatch({
				filePaths: source.value.files,
				ttsBaseSpeed: speed.value,
				burnSubtitles: false,
				keepMemes: keepMemes.value,
				uniquify: true,
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
				burnSubtitles: false,
				keepMemes: keepMemes.value,
				uniquify: true,
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
	<div class="w-full flex-1 flex flex-col max-w-3xl mx-auto gap-8 pt-6">
		<!-- 1. Фокусный Omnibox -->
		<div
			class="w-full rounded-2xl flex flex-col p-3 transition-all"
			style="background: var(--bg-secondary)"
		>
			<!-- Строка ввода -->
			<div class="flex items-center gap-3 px-2 py-1">
				<!-- Токен выбранного файла / папки -->
				<div
					v-if="source"
					class="flex items-center gap-2 px-2.5 py-1 rounded-lg text-xs"
					style="background: var(--bg-tertiary); color: var(--text-primary)"
				>
					<Icon
						:name="source.type === 'folder' ? 'folder' : 'video'"
						class="w-4 h-4 text-[var(--accent)]"
					/>
					<span class="font-medium max-w-xs truncate">{{ source.name }}</span>
					<span v-if="source.count" class="text-[11px] font-mono text-[var(--text-muted)]">
						{{ source.count }} видео
					</span>
					<button
						type="button"
						@click="resetSource"
						class="p-0.5 hover:text-white text-[var(--text-muted)] bg-transparent border-none cursor-pointer"
						title="Сбросить"
					>
						<Icon name="close" class="w-3.5 h-3.5" />
					</button>
				</div>

				<!-- Поле ввода URL -->
				<input
					v-else
					ref="inputRef"
					v-model="url"
					type="text"
					placeholder="Вставьте ссылку на Shorts, Reels, TikTok или выберите файл..."
					class="w-full bg-transparent border-none outline-none text-sm text-[var(--text-primary)] placeholder-[var(--text-muted)] py-1"
				/>

				<!-- Иконки выбора файла / папки -->
				<div class="flex items-center gap-1 shrink-0">
					<button
						type="button"
						@click="handlePickFile"
						class="p-1.5 rounded-lg text-[var(--text-muted)] hover:text-white hover:bg-[var(--bg-tertiary)] bg-transparent border-none cursor-pointer transition-colors"
						title="Выбрать видеофайл (⌘O)"
					>
						<Icon name="video" class="w-4 h-4" />
					</button>
					<button
						type="button"
						@click="handlePickFolder"
						class="p-1.5 rounded-lg text-[var(--text-muted)] hover:text-white hover:bg-[var(--bg-tertiary)] bg-transparent border-none cursor-pointer transition-colors"
						title="Выбрать папку (⌘⇧O)"
					>
						<Icon name="folder" class="w-4 h-4" />
					</button>
				</div>
			</div>

			<!-- Нижняя строка: кнопка запуска -->
			<div class="flex items-center justify-end pt-2 px-2 text-xs">
				<!-- Кнопка запуска перевода (Shadcn Button) -->
				<Button :disabled="!canStart" @click="handleStart" size="sm" class="gap-2">
					<Icon v-if="isSubmitting" name="reload" class="w-3.5 h-3.5 animate-spin" />
					<Icon v-else name="star" class="w-3.5 h-3.5" />
					<span>{{
						source?.type === 'folder' ? `Перевести ${source.count} видео` : 'Перевести видео'
					}}</span>
					<Kbd class="opacity-70 border-black/20 bg-black/10 text-black">⌘↵</Kbd>
				</Button>
			</div>
		</div>

		<!-- 2. Очередь активных задач -->
		<div v-if="activeTasks.length > 0" class="flex flex-col gap-2">
			<span class="text-[11px] font-mono text-[var(--text-muted)] uppercase tracking-wider px-1">
				В обработке ({{ activeTasks.length }})
			</span>

			<div class="flex flex-col gap-1.5">
				<div
					v-for="task in activeTasks"
					:key="task.id"
					@click="router.push({ name: 'processing', params: { id: task.id } })"
					class="flex flex-col p-3 rounded-xl cursor-pointer transition-all hover:bg-[var(--bg-tertiary)] relative overflow-hidden"
					style="background: var(--bg-secondary)"
				>
					<div class="flex items-center justify-between">
						<div class="flex items-center gap-3 min-w-0">
							<FileVideoIcon class="w-4 h-4 text-[var(--accent)] shrink-0" />
							<span class="text-xs font-medium text-white truncate">
								{{ task.info?.title || task.id }}
							</span>
						</div>

						<div class="flex items-center gap-3 shrink-0 ml-3">
							<span class="text-[11px] font-mono text-[var(--text-muted)]">
								{{
									task.current_stage
										? STAGE_NAMES[task.current_stage as StageName] || task.current_stage
										: 'Подготовка'
								}}
							</span>
							<span class="text-xs font-mono text-white">{{ getStageProgress(task) }}%</span>
						</div>
					</div>

					<!-- Полоса прогресса внизу строки -->
					<div
						class="absolute bottom-0 left-0 right-0 h-[2px]"
						style="background: var(--bg-tertiary)"
					>
						<div
							class="h-full transition-all duration-300"
							style="background: var(--accent)"
							:style="{ width: `${getStageProgress(task)}%` }"
						/>
					</div>
				</div>
			</div>
		</div>

		<!-- 3. Недавние готовые видео -->
		<div v-if="recentDoneTasks.length > 0" class="flex flex-col gap-2">
			<div class="flex items-center justify-between px-1">
				<span class="text-[11px] font-mono text-[var(--text-muted)] uppercase tracking-wider">
					Недавние
				</span>
				<button
					type="button"
					@click="router.push({ name: 'history' })"
					class="text-[11px] text-[var(--text-muted)] hover:text-white bg-transparent border-none cursor-pointer p-0"
				>
					Все →
				</button>
			</div>

			<div class="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
				<div
					v-for="done in recentDoneTasks"
					:key="done.id"
					@click="router.push({ name: 'result', params: { id: done.id } })"
					class="flex flex-col p-2 rounded-xl cursor-pointer transition-all hover:bg-[var(--bg-tertiary)] group"
					style="background: var(--bg-secondary)"
				>
					<div
						class="w-full aspect-[9/16] max-h-36 rounded-lg mb-2 overflow-hidden flex items-center justify-center relative"
						style="background: var(--bg-tertiary)"
					>
						<img
							v-if="done.info?.thumbnail"
							:src="done.info.thumbnail"
							class="w-full h-full object-cover"
						/>
						<Icon v-else name="video" class="w-6 h-6 text-[var(--text-muted)]" />
						<div
							class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity"
						>
							<Icon name="play" class="w-5 h-5 text-white" />
						</div>
					</div>
					<span class="text-xs text-white truncate">
						{{ done.info?.title || done.id }}
					</span>
				</div>
			</div>
		</div>
	</div>
</template>
