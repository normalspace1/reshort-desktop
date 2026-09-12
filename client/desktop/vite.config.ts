import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import path from 'node:path'

// https://vite.dev/config/
export default defineConfig({
	plugins: [vue(), tailwindcss()],
	resolve: {
		alias: {
			'@': path.resolve(import.meta.dirname, './src'),
		},
	},
	server: {
		host: '127.0.0.1',
		port: 5173,
		strictPort: true,
		watch: {
			ignored: ['**/src-tauri/**'],
		},
	},
	test: {
		environment: 'node',
		include: ['src/**/*.spec.ts'],
	},
})
