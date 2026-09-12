function pad2(value: number): string {
	return String(value).padStart(2, '0')
}

export function formatDate(iso?: string): string {
	if (!iso) return ''
	const date = new Date(iso)
	if (Number.isNaN(date.getTime())) return ''
	return `${pad2(date.getDate())}.${pad2(date.getMonth() + 1)}.${date.getFullYear()}`
}

export function formatTimestamp(iso?: string): string {
	if (!iso) return ''
	const date = new Date(iso)
	if (Number.isNaN(date.getTime())) return ''
	return `${pad2(date.getDate())}.${pad2(date.getMonth() + 1)}.${date.getFullYear()} ${pad2(date.getHours())}:${pad2(date.getMinutes())}`
}

export function formatBytes(bytes: number): string {
	if (bytes >= 1024 * 1024 * 1024) return (bytes / (1024 * 1024 * 1024)).toFixed(1) + ' ГБ'
	if (bytes >= 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' МБ'
	if (bytes >= 1024) return (bytes / 1024).toFixed(0) + ' КБ'
	return bytes + ' Б'
}
