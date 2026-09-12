import { createRouter, createWebHashHistory } from 'vue-router'

const router = createRouter({
	history: createWebHashHistory(),
	routes: [
		{ path: '/', redirect: '/queue' },
		{
			path: '/queue',
			name: 'queue',
			component: () => import('@/views/QueueView.vue'),
			meta: { title: 'Очередь' },
		},
		{
			path: '/new',
			redirect: '/queue',
		},
		{
			path: '/processing/:id',
			name: 'processing',
			component: () => import('@/views/ProcessingView.vue'),
			meta: { title: 'Обработка' },
		},
		{
			path: '/result/:id',
			name: 'result',
			component: () => import('@/views/ResultView.vue'),
			meta: { title: 'Результат' },
		},
		{
			path: '/history',
			name: 'history',
			component: () => import('@/views/HistoryView.vue'),
			meta: { title: 'Контент' },
		},
		{ path: '/presets', redirect: '/queue' },
		{ path: '/settings', redirect: '/queue' },
		{ path: '/projects', redirect: '/history' },
		{
			path: '/projects/:id',
			redirect: (to) => `/processing/${to.params.id}`,
		},
		{ path: '/:pathMatch(.*)*', redirect: '/queue' },
	],
})

export default router
