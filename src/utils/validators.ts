export interface UrlValidation {
	isValid: boolean
	platform?: string
	error?: string
}

export const validateVideoUrl = (url: string): UrlValidation => {
	if (!url || !url.trim()) {
		return { isValid: false, error: 'Ссылка не может быть пустой' }
	}

	let parsedUrl: URL
	try {
		parsedUrl = new URL(url.trim())
	} catch {
		return {
			isValid: false,
			error: 'Неверный формат ссылки (введите полный URL, начиная с https://)',
		}
	}

	const hostname = parsedUrl.hostname.toLowerCase()

	// YouTube (Standard and Shorts)
	if (hostname.includes('youtube.com') || hostname.includes('youtu.be')) {
		if (
			parsedUrl.pathname.includes('/watch') ||
			parsedUrl.pathname.includes('/shorts/') ||
			hostname.includes('youtu.be')
		) {
			return { isValid: true, platform: 'YouTube' }
		}
		return { isValid: false, error: 'Ссылка должна вести на конкретное видео или Shorts' }
	}

	// TikTok
	if (hostname.includes('tiktok.com')) {
		return { isValid: true, platform: 'TikTok' }
	}

	// Instagram (Reels)
	if (hostname.includes('instagram.com')) {
		if (
			parsedUrl.pathname.includes('/reels/') ||
			parsedUrl.pathname.includes('/reel/') ||
			parsedUrl.pathname.includes('/p/')
		) {
			return { isValid: true, platform: 'Instagram' }
		}
		return { isValid: false, error: 'Ссылка должна вести на конкретный Reel или пост' }
	}

	// VK Video / Clips
	if (hostname.includes('vk.com') || hostname.includes('vk.video')) {
		if (
			parsedUrl.pathname.includes('/video') ||
			parsedUrl.pathname.includes('/clip') ||
			parsedUrl.searchParams.has('z')
		) {
			return { isValid: true, platform: 'VK' }
		}
		return { isValid: false, error: 'Ссылка должна вести на конкретное видео или клип ВКонтакте' }
	}

	return {
		isValid: false,
		error: 'Платформа не поддерживается. Поддерживаются только YouTube, TikTok, Instagram и VK.',
	}
}
