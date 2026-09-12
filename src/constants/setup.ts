export const PREFLIGHT_LABELS: Record<string, string> = {
	ffmpeg: 'FFmpeg',
	ffprobe: 'FFprobe',
	ytdlp: 'yt-dlp',
	models: 'Модель разделения',
	worker: 'Worker :8000',
}

export const PREFLIGHT_ERRORS: Record<string, string> = {
	error_ffmpeg: 'Не найден',
	error_ffprobe: 'Не найден',
	error_ytdlp: 'Не найден',
	error_models: 'Не загружена',
	error_worker: 'Не отвечает',
}
