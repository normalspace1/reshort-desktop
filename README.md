# ReVoice Desktop (ReShort) 🎙️

Десктопное приложение для автоматического AI-дубляжа коротких вертикальных видео (YouTube Shorts, TikTok, Instagram Reels, VK Клипы).

Разработано на **Tauri v2** + **Vue 3** (TypeScript, Tailwind CSS v4, Shadcn-Vue).

---

## ⚡ Особенности Desktop-приложения

- **Минималистичный macOS-интерфейс**: центрированная шапка (TopNav), палитра команд (`⌘K`), Omnibox с хоткеями (`⌘↵`).
- **Автоматический Zero-Shot Voice Clone**: клонирование голоса оригинального спикера (Fish Audio).
- **Пакетная обработка**: поддержка одиночных файлов, ссылок и целых директорий с видео.
- **Встроенный вертикальный 9:16 видеоплеер**: просмотр с таймлайном, скруббером и скачиванием MP4 в один клик.
- **Preflight Setup**: проверка и автоматическая подгрузка окружения (FFmpeg, yt-dlp, UVR-MDX-Net).

---

## 🚀 Запуск и разработка

### Требования
- Node.js 20+
- Rust (stable toolchain)
- Visual Studio Build Tools (C++ / Windows SDK)

### Установка зависимостей

```bash
cd client/desktop
npm install
```

### Режим разработки

```bash
npm run tauri dev
```

### Сборка production

```bash
npm run tauri build
```
