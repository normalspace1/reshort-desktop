# ReVoice (ReShort) 🎙️

**ReVoice** — десктопное приложение для автоматического перевода и переозвучки (дубляжа) видео (YouTube, TikTok, Instagram, VK и др.) с сохранением оригинальной фоновой музыки, интершумов и синхронизацией речи.

---

## 🏗 Архитектура

Проект разделён на 3 независимых компонента:

```
revoice/
├── client/desktop/    # Десктопный GUI на Tauri v2 (Rust) + Vue 3 (TypeScript, Tailwind v4, Shadcn)
├── worker/            # Локальный Python-воркер мультимедийного пайплайна (FastAPI, FFmpeg, UVR)
└── server/            # Бэкенд-шлюз для облачных нейросетей (NestJS, Groq, Gemini, Fish Audio)
```

### 1. Десктопный клиент (client/desktop)
- **Tauri v2 + Vue 3** (Composition API, Pinia, Tailwind CSS v4, Lucide).
- Минималистичный интерфейс в стиле macOS (TopNav, Command Palette ⌘K, Omnibox).
- Управление жизненным циклом фонового воркера.
- Preflight-чекер: автоматическая проверка и загрузка зависимостей (FFmpeg, FFprobe, yt-dlp, ONNX-модель Kim_Vocal_2).
- Скачивание видео с видеохостингов через yt-dlp или выбор локальных файлов/папок.
- Встроенный 9:16 видеоплеер, история и просмотр готовых проектов.

### 2. Локальный воркер пайплайна (worker)
Конвейер обработки:
1. `download` — скачивание видеопотока высокого качества.
2. `separate` — разделение вокала и музыки с помощью модели Kim_Vocal_2.onnx (UVR-MDX-Net).
3. `transcribe` — транскрибация аудио с временными метками слов (Word-level timestamps) через Groq Whisper.
4. `translate` — группировка слов в субтитровые фразы, перевод на целевой язык (Google Gemini), адаптация текста под хронометраж и естественную речь дубляжа.
5. `tts` — генерация голоса и zero-shot клонирование тембра через Fish Audio.
6. `mix` — динамический сайдчейн-дакинг (приглушение фоновой музыки под голос) и мастеринг по стандарту EBU R128 (-14 LUFS).
7. `finalize` — сборка и экспорт итогового MP4-видео.

### 3. Сервер-шлюз (server)
- **NestJS 12 + TypeScript**.
- Централизованное хранение API-ключей и проксирование вызовов:
  - **Groq API**: Whisper транскрипция.
  - **Google Gemini API**: перевод и адаптация текста под дубляж.
  - **Fish Audio API**: синтез речи и клонирование голоса.

---

## 🚀 Быстрый старт

### 1. Настройка и запуск Сервера ИИ

```bash
cd server
npm install
cp .env.example .env
# Укажите ваши ключи GEMINI_API_KEY, GROQ_API_KEY, FISH_AUDIO_API_KEY в файле .env
npm run start:dev
```

### 2. Запуск Воркера (Python)

```bash
# В корне проекта:
python -m worker.server
```

### 3. Запуск Десктопного приложения

```bash
cd client/desktop
npm install
npm run tauri dev
```

При первом запуске клиент автоматически проверит наличие FFmpeg, yt-dlp и нейросетевых моделей в `%APPDATA%/Reshort` и при необходимости загрузит недостающие файлы.
