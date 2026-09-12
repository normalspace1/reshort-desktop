<script lang="ts" setup>
import {
	CircleCheckIcon,
	InfoIcon,
	Loader2Icon,
	OctagonXIcon,
	TriangleAlertIcon,
	XIcon,
} from '@lucide/vue'
import { reactiveOmit } from '@vueuse/core'
import { Toaster as Sonner, type ToasterProps } from 'vue-sonner'

import { cn } from '@/lib/utils'

const props = defineProps<ToasterProps>()
const delegatedProps = reactiveOmit(props, 'class', 'toastOptions')
</script>

<template>
	<Sonner
		:class="cn('toaster group', props.class)"
		:style="{
			'--normal-bg': 'var(--bg-tertiary)',
			'--normal-text': 'var(--text-primary)',
			'--normal-border': 'var(--border-strong)',
			'--border-radius': 'var(--radius-xl)',

			'--success-bg': 'var(--bg-tertiary)',
			'--success-border': 'var(--border-strong)',
			'--success-text': 'var(--text-primary)',

			'--error-bg': 'var(--bg-tertiary)',
			'--error-border': 'var(--border-strong)',
			'--error-text': 'var(--text-primary)',

			'--info-bg': 'var(--bg-tertiary)',
			'--info-border': 'var(--border-strong)',
			'--info-text': 'var(--text-primary)',
		}"
		:toast-options="
			props.toastOptions ?? {
				classes: {
					toast: 'compact-toast flex items-center',
					title: 'text-[12px] font-medium leading-none',
					description: 'text-[11px] text-[var(--text-muted)] leading-tight mt-0.5',
					icon: 'mr-1.5',
				},
			}
		"
		v-bind="delegatedProps"
	>
		<template #success-icon>
			<CircleCheckIcon class="w-3.5 h-3.5 text-[#0A84FF]" />
		</template>
		<template #info-icon>
			<InfoIcon class="w-3.5 h-3.5 text-[#0A84FF]" />
		</template>
		<template #warning-icon>
			<TriangleAlertIcon class="w-3.5 h-3.5 text-[#F59E0B]" />
		</template>
		<template #error-icon>
			<OctagonXIcon class="w-3.5 h-3.5 text-[#E63946]" />
		</template>
		<template #loading-icon>
			<div class="text-[var(--text-primary)]">
				<Loader2Icon class="w-3.5 h-3.5 animate-spin" />
			</div>
		</template>
		<template #close-icon>
			<XIcon class="w-3 h-3 opacity-70 hover:opacity-100" />
		</template>
	</Sonner>
</template>

<style>
/* Максимально компактные тостеры-пилюли */
.compact-toast {
	padding: 6px 12px !important;
	min-height: 32px !important;
	gap: 6px !important;
	width: auto !important;
	min-width: 0 !important; /* Убираем фиксированную ширину, пусть сжимается по тексту */
	border: none !important;
	border-radius: 99px !important; /* Идеальная форма капсулы */
	box-shadow: none !important;
	background-color: var(--bg-tertiary) !important;
	color: var(--text-primary) !important;
}

.compact-toast [data-icon] {
	display: flex !important;
	align-items: center;
	justify-content: center;
}

/* Скрываем дополнительный текст (description), чтобы тостер всегда был в одну строку */
[data-sonner-toast] [data-description] {
	display: none !important;
}
</style>
