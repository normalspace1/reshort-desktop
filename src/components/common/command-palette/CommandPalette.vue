<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Icon } from '@/components/ui'

import { filePickerApi } from '@/api/projects'
import { useProjectStore } from '@/stores/project'

const emit = defineEmits<{
	(e: 'close'): void
	(e: 'select-file', path: string): void
	(e: 'select-folder', path: string): void
}>()

const store = useProjectStore()
const router = useRouter()
const query = ref('')
const selectedIndex = ref(0)
const searchInput = ref<HTMLInputElement | null>(null)

interface CommandItem {
	id: string
	title: string
	subtitle?: string
	icon: string
	shortcut?: string
	category: 'Создание' | 'Навигация'
	action: () => void | Promise<void>
}

const commands = computed<CommandItem[]>(() => {
	const list: CommandItem[] = [
		{
			id: 'new',
			title: 'Новый проект дубляжа',
			subtitle: 'Вставить ссылку или выбрать файл',
			icon: 'add',
			shortcut: '⌘N',
			category: 'Создание',
			action: () => {
				router.push({ name: 'queue' })
				emit('close')
			},
		},
		{
			id: 'open-file',
			title: 'Выбрать видеофайл...',
			subtitle: 'MP4, MOV, MKV, WebM',
			icon: 'video',
			shortcut: '⌘O',
			category: 'Создание',
			action: async () => {
				emit('close')
				try {
					const file = await filePickerApi.pickFile()
					if (file) {
						emit('select-file', file)
						router.push({ name: 'queue' })
					}
				} catch (e) {
					console.error(e)
				}
			},
		},
		{
			id: 'open-folder',
			title: 'Выбрать папку (пакетный дубляж)...',
			subtitle: 'Перевести все ролики в папке',
			icon: 'folder',
			shortcut: '⌘⇧O',
			category: 'Создание',
			action: async () => {
				emit('close')
				try {
					const folder = await filePickerApi.pickFolder()
					if (folder) {
						emit('select-folder', folder)
						router.push({ name: 'queue' })
					}
				} catch (e) {
					console.error(e)
				}
			},
		},
		{
			id: 'goto-queue',
			title: 'Перейти в очередь',
			subtitle: `${store.queueCount} активных задач`,
			icon: 'channel',
			shortcut: '⌘1',
			category: 'Навигация',
			action: () => {
				router.push({ name: 'queue' })
				emit('close')
			},
		},
		{
			id: 'goto-history',
			title: 'Перейти в историю',
			subtitle: `${store.historyCount} готовых видео`,
			icon: 'recent',
			shortcut: '⌘2',
			category: 'Навигация',
			action: () => {
				router.push({ name: 'history' })
				emit('close')
			},
		},
	]

	if (!query.value.trim()) return list

	const q = query.value.toLowerCase().trim()
	return list.filter(
		(c) =>
			c.title.toLowerCase().includes(q) ||
			(c.subtitle && c.subtitle.toLowerCase().includes(q)) ||
			c.category.toLowerCase().includes(q),
	)
})

watch(query, () => {
	selectedIndex.value = 0
})

function handleKeyDown(e: KeyboardEvent) {
	if (e.key === 'ArrowDown') {
		e.preventDefault()
		selectedIndex.value = (selectedIndex.value + 1) % commands.value.length
	} else if (e.key === 'ArrowUp') {
		e.preventDefault()
		selectedIndex.value = (selectedIndex.value - 1 + commands.value.length) % commands.value.length
	} else if (e.key === 'Enter') {
		e.preventDefault()
		const selected = commands.value[selectedIndex.value]
		if (selected) {
			selected.action()
		}
	} else if (e.key === 'Escape') {
		e.preventDefault()
		emit('close')
	}
}

onMounted(() => {
	searchInput.value?.focus()
	window.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
	window.removeEventListener('keydown', handleKeyDown)
})
</script>

<template>
	<div
		class="fixed inset-0 z-50 flex items-start justify-center pt-24 px-4"
		style="background: rgba(0, 0, 0, 0.72); backdrop-filter: blur(8px)"
		@click.self="emit('close')"
	>
		<div
			class="w-full max-w-xl rounded-2xl overflow-hidden shadow-2xl flex flex-col transition-all"
			style="
				background: var(--bg-secondary);
				border: 1px solid var(--border-default);
				box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6);
			"
		>
			<!-- Строка поиска -->
			<div
				class="flex items-center gap-3 px-4 py-3.5 border-b"
				style="border-color: var(--border-divider)"
			>
				<Icon name="search" class="w-4 h-4 text-white" />
				<input
					ref="searchInput"
					v-model="query"
					type="text"
					placeholder="Введите команду или поиск..."
					class="w-full bg-transparent border-none outline-none text-sm text-[var(--text-primary)] placeholder-[var(--text-muted)]"
				/>
				<span
					class="text-[10px] font-mono px-1.5 py-0.5 rounded text-[var(--text-muted)]"
					style="background: var(--bg-tertiary)"
				>
					Esc
				</span>
			</div>

			<!-- Список команд -->
			<div class="max-h-[340px] overflow-y-auto py-2 px-1.5 flex flex-col gap-0.5">
				<div v-if="commands.length === 0" class="py-8 text-center text-xs text-[var(--text-muted)]">
					Ничего не найдено по запросу «{{ query }}»
				</div>

				<button
					v-for="(item, idx) in commands"
					:key="item.id"
					type="button"
					@click="item.action()"
					@mouseenter="selectedIndex = idx"
					class="flex items-center justify-between w-full px-3 py-2 rounded-lg text-left cursor-pointer border-none transition-colors"
					:class="
						selectedIndex === idx
							? 'bg-[var(--bg-tertiary)] text-white'
							: 'bg-transparent text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]'
					"
				>
					<div class="flex items-center gap-3 min-w-0">
						<Icon :name="item.icon" class="w-4 h-4 shrink-0 text-white" />
						<div class="flex flex-col min-w-0">
							<span
								class="text-xs font-medium truncate"
								:class="selectedIndex === idx ? 'text-white' : ''"
							>
								{{ item.title }}
							</span>
							<span v-if="item.subtitle" class="text-[11px] truncate text-[var(--text-muted)]">
								{{ item.subtitle }}
							</span>
						</div>
					</div>

					<div class="flex items-center gap-2 shrink-0 ml-3">
						<span
							v-if="item.shortcut"
							class="text-[10px] font-mono px-1.5 py-0.5 rounded text-[var(--text-muted)]"
							style="background: var(--bg-primary)"
						>
							{{ item.shortcut }}
						</span>
					</div>
				</button>
			</div>

			<!-- Нижняя строка подсказок -->
			<div
				class="flex items-center justify-between px-4 py-2 text-[11px] font-mono border-t"
				style="
					border-color: var(--border-divider);
					color: var(--text-muted);
					background: var(--bg-primary);
				"
			>
				<div class="flex items-center gap-3">
					<span><span class="text-white">↑↓</span> навигация</span>
					<span><span class="text-white">↵</span> выбор</span>
					<span><span class="text-white">esc</span> закрыть</span>
				</div>
			</div>
		</div>
	</div>
</template>
