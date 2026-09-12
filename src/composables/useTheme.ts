import { ref } from 'vue'

export type ThemeName = 'zed' | 'oled'

export interface ThemeOption {
	id: ThemeName
	name: string
	description: string
	accentColor: string
	bgPreview: string
}

export const THEME_OPTIONS: ThemeOption[] = [
	{
		id: 'zed',
		name: 'Zed Carbon',
		description: 'Фирменный графитово-угольный стиль Zed с акцентами One Dark',
		accentColor: '#4aa5f0',
		bgPreview: '#181a1f',
	},
	{
		id: 'oled',
		name: 'OLED Black',
		description: 'Глубокий чёрный минимализм с контрастными белыми акцентами',
		accentColor: '#ffffff',
		bgPreview: '#0a0a0a',
	},
]

const stored =
	(typeof localStorage !== 'undefined' && (localStorage.getItem('reshort-theme') as ThemeName)) ||
	'zed'
const currentTheme = ref<ThemeName>(stored)

export function useTheme() {
	function applyTheme(t: ThemeName) {
		currentTheme.value = t
		try {
			localStorage.setItem('reshort-theme', t)
		} catch {}
		if (typeof document !== 'undefined') {
			document.documentElement.setAttribute('data-theme', t)
		}
	}

	function initTheme() {
		applyTheme(currentTheme.value)
	}

	return {
		theme: currentTheme,
		setTheme: applyTheme,
		initTheme,
		themes: THEME_OPTIONS,
	}
}
