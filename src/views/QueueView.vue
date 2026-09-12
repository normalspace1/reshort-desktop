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

const isVerticalMap = ref<Record<string, boolean>>({})

function onImgLoad(e: Event, id: string) {
	const img = e.target as HTMLImageElement
	if (img && img.naturalWidth && img.naturalHeight) {
		isVerticalMap.value[id] = img.naturalHeight > img.naturalWidth
	}
}

function isVertical(p: any): boolean {
	if (isVerticalMap.value[p.id] !== undefined) {
		return isVerticalMap.value[p.id]
	}
	if (p.info?.resolution) {
		const [w, h] = p.info.resolution.split('x').map(Number)
		if (w && h) return h > w
	}
	return true
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
					class="flex items-center gap-2.5 flex-1 min-w-0 px-3.5 py-2 rounded-xl bg-white/5"
				>
					<Icon name="search" class="w-4 h-4 text-white shrink-0 opacity-70" />
					<input
						ref="inputRef"
						v-model="url"
						type="text"
						placeholder="Вставьте ссылку Shorts, Reels, TikTok или выберите файл..."
						class="w-full bg-transparent border-none outline-none text-xs text-white placeholder:text-[var(--text-muted)]"
					/>
				</div>

				<!-- Кнопки выбора файлов -->
				<div class="flex items-center gap-1.5 shrink-0">
					<button
						type="button"
						@click="handlePickFile"
						class="flex items-center gap-1.5 px-3.5 py-2 rounded-full text-xs font-medium text-white hover:bg-white/10 bg-white/5 border-none cursor-pointer transition-colors"
						title="Выбрать файл (⌘O)"
					>
						<Icon name="video" class="w-3.5 h-3.5 text-white" />
						<span>Файл</span>
					</button>
					<button
						type="button"
						@click="handlePickFolder"
						class="flex items-center gap-1.5 px-3.5 py-2 rounded-full text-xs font-medium text-white hover:bg-white/10 bg-white/5 border-none cursor-pointer transition-colors"
						title="Выбрать папку (⌘⇧O)"
					>
						<Icon name="folder" class="w-3.5 h-3.5 text-white" />
						<span>Папка</span>
					</button>
				</div>
			</div>

			<!-- Нижняя строка: настройки и запуск -->
			<div class="flex flex-wrap items-center justify-between gap-4 pt-1 text-xs">
				<div class="flex flex-wrap items-center gap-5 text-[var(--text-secondary)]">
					<!-- Скорость речи -->
					<div class="flex items-center gap-1.5">
						<span class="text-[11px] text-[var(--text-muted)]">Темп:</span>
						<div class="flex items-center gap-1">
							<button
								v-for="s in [1.0, 1.12, 1.25]"
								:key="s"
								type="button"
								@click="speed = s"
								class="px-2.5 py-1 rounded-full text-xs font-medium border-none cursor-pointer transition-all"
								:class="
									speed === s
										? 'bg-white text-[#0f0f0f]'
										: 'bg-transparent text-[var(--text-secondary)] hover:text-white hover:bg-white/5'
								"
							>
								{{ s }}x
							</button>
						</div>
					</div>

					<div class="h-3.5 w-px bg-white/10 hidden sm:block" />

					<!-- Тумблеры -->
					<label class="flex items-center gap-2 cursor-pointer hover:text-white transition-colors">
						<Switch v-model="keepMemes" />
						<span class="text-xs">Фоновый звук</span>
					</label>

					<label class="flex items-center gap-2 cursor-pointer hover:text-white transition-colors">
						<Switch v-model="burnSubtitles" />
						<span class="text-xs">Субтитры</span>
					</label>

					<label class="flex items-center gap-2 cursor-pointer hover:text-white transition-colors">
						<Switch v-model="uniquify" />
						<span class="text-xs">Антидетект</span>
					</label>
				</div>

				<!-- Кнопка запуска -->
				<div class="ml-auto">
					<Button :disabled="!canStart" @click="handleStart" class="px-5 h-9 font-medium gap-2">
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
			<div class="flex items-center justify-between px-1">
				<span class="text-xs font-medium text-[var(--text-secondary)]">
					Очередь обработки ({{ activeTasks.length }})
				</span>
			</div>

			<div class="w-full flex flex-col gap-2">
				<div
					v-for="task in activeTasks"
					:key="task.id"
					@click="router.push({ name: 'processing', params: { id: task.id } })"
					class="flex items-center justify-between p-4 rounded-2xl cursor-pointer transition-all hover:bg-[var(--bg-hover)] relative"
					style="background: var(--bg-secondary)"
				>
					<div class="flex items-center gap-3.5 min-w-0 flex-1">
						<Icon name="video" class="w-5 h-5 text-white shrink-0" />
						<div class="flex flex-col min-w-0">
							<span class="text-xs font-medium text-white truncate">
								{{ task.info?.title || task.id }}
							</span>
							<span class="text-[11px] text-[var(--text-secondary)] mt-0.5">
								{{
									task.current_stage
										? STAGE_NAMES[task.current_stage as StageName] || task.current_stage
										: 'Обработка...'
								}}
							</span>
						</div>
					</div>

					<div class="flex items-center gap-4 shrink-0 ml-4">
						<div class="w-28 flex flex-col gap-1 items-end">
							<span class="text-xs text-white font-mono font-medium">
								{{ getStageProgress(task) }}%
							</span>
							<div class="h-1 w-full rounded-full overflow-hidden bg-white/10">
								<div
									class="h-full transition-all duration-300 rounded-full bg-white"
									:style="{ width: `${getStageProgress(task)}%` }"
								/>
							</div>
						</div>

						<Icon name="arrow-right" class="w-4 h-4 text-white opacity-70" />
					</div>
				</div>
			</div>
		</div>

		<!-- 3. Недавние готовые результаты -->
		<div v-if="recentDoneTasks.length > 0" class="flex flex-col gap-2.5">
			<div class="flex items-center justify-between px-1">
				<span class="text-xs font-medium text-[var(--text-secondary)]">Готовые видео</span>
				<button
					type="button"
					@click="router.push({ name: 'history' })"
					class="text-xs text-[var(--text-secondary)] hover:text-white bg-transparent border-none cursor-pointer p-0 transition-colors"
				>
					Весь контент →
				</button>
			</div>

			<div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
				<div
					v-for="done in recentDoneTasks"
					:key="done.id"
					@click="router.push({ name: 'result', params: { id: done.id } })"
					class="flex items-center gap-3 p-2.5 rounded-2xl cursor-pointer transition-all hover:bg-[var(--bg-hover)] group"
					style="background: var(--bg-secondary)"
				>
					<div
						class="h-14 rounded-lg overflow-hidden shrink-0 flex items-center justify-center relative bg-black/60"
						:class="isVertical(done) ? 'w-9 aspect-[9/16]' : 'w-20 aspect-video'"
					>
						<img
							v-if="done.info?.thumbnail"
							:src="done.info.thumbnail"
							@load="onImgLoad($event, done.id)"
							class="w-full h-full object-cover"
						/>
						<Icon v-else name="video" class="w-4 h-4 text-white" />
						<div
							class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity"
						>
							<Icon name="play" class="w-4 h-4 text-white" />
						</div>
					</div>
					<div class="flex flex-col min-w-0 flex-1">
						<span class="text-xs font-medium text-white truncate">
							{{ done.info?.title || done.id }}
						</span>
						<span class="text-[11px] text-[var(--text-secondary)] mt-0.5"> Готово к экспорту </span>
					</div>
					<Icon
						name="arrow-right"
						class="w-4 h-4 text-white opacity-40 group-hover:opacity-100 mr-1 transition-opacity shrink-0"
					/>
				</div>
			</div>
		</div>
	</div>
</template>
