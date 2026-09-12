import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';

@Injectable()
export class HealthService {
  constructor(private configService: ConfigService) {}

  async checkServices() {
    const results: Record<string, any> = {
      gemini: { status: 'unknown' },
      groq: { status: 'unknown' },
      fishAudio: { status: 'unknown' },
    };

    let allOk = true;

    // Проверка Gemini
    try {
      const geminiKey = this.configService.get<string>('gemini.apiKey');
      if (!geminiKey || geminiKey.includes('your-')) {
        results.gemini = { status: 'error', message: 'API key not configured' };
        allOk = false;
      } else {
        const res = await fetch(
          `https://generativelanguage.googleapis.com/v1beta/models?key=${geminiKey}`,
          { signal: AbortSignal.timeout(5000) },
        );
        if (res.ok) {
          results.gemini = { status: 'ok' };
        } else {
          const err = await res.json().catch(() => ({}));
          results.gemini = {
            status: 'error',
            message: err.error?.message || res.statusText,
          };
          allOk = false;
        }
      }
    } catch (e: any) {
      results.gemini = { status: 'error', message: e.message };
      allOk = false;
    }

    // Проверка Groq
    try {
      const groqKey = this.configService.get<string>('groq.apiKey');
      if (!groqKey || groqKey.includes('your-')) {
        results.groq = { status: 'error', message: 'API key not configured' };
        allOk = false;
      } else {
        const res = await fetch('https://api.groq.com/openai/v1/models', {
          headers: { Authorization: `Bearer ${groqKey}` },
        });
        if (res.ok) {
          results.groq = { status: 'ok' };
        } else {
          const err = await res.json().catch(() => ({}));
          results.groq = {
            status: 'error',
            message: err.error?.message || res.statusText,
          };
          allOk = false;
        }
      }
    } catch (e: any) {
      results.groq = { status: 'error', message: e.message };
      allOk = false;
    }

    // Проверка Fish Audio
    try {
      const fishKey = this.configService.get<string>('fishAudio.apiKey');
      if (!fishKey || fishKey.includes('your-')) {
        results.fishAudio = {
          status: 'error',
          message: 'API key not configured',
        };
        allOk = false;
      } else {
        // Отправляем фейковый запрос, чтобы проверить токен.
        // Fish API ответит 401 Unauthorized, если ключ неверный, и 400 Bad Request, если запрос кривой (но ключ верный)
        const res = await fetch('https://api.fish.audio/v1/tts', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${fishKey}`,
          },
          body: JSON.stringify({ text: 'test' }),
        });

        if (res.status === 401 || res.status === 403) {
          results.fishAudio = {
            status: 'error',
            message: 'Invalid API Key or Unauthorized',
          };
          allOk = false;
        } else {
          // Если 200 или 400 (ошибка валидации payload'a, но авторизация прошла), считаем, что связь есть
          results.fishAudio = { status: 'ok' };
        }
      }
    } catch (e: any) {
      results.fishAudio = { status: 'error', message: e.message };
      allOk = false;
    }

    return {
      status: allOk ? 'ok' : 'degraded',
      timestamp: new Date().toISOString(),
      services: results,
    };
  }
}
