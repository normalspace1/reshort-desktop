import { Injectable, InternalServerErrorException, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { readPrompts } from '../../../common/config/configuration.js';

@Injectable()
export class TranslateService {
  private readonly logger = new Logger(TranslateService.name);

  constructor(private configService: ConfigService) {}

  async process(data: any) {
    const startTime = Date.now();
    const apiKey = this.configService.get<string>('gemini.apiKey');
    const baseUrl = (
      this.configService.get<string>('gemini.apiUrl') ||
      'https://generativelanguage.googleapis.com/v1beta'
    ).replace(/\/openai$/, '');
    const model =
      data.model ||
      this.configService.get<string>('gemini.model') ||
      'gemini-flash-latest';

    if (!apiKey) {
      this.logger.error('GEMINI_API_KEY is missing in server configuration');
      throw new InternalServerErrorException(
        'GEMINI_API_KEY is not configured',
      );
    }

    const targetLang = data.target_lang || 'ru';
    const langMap: Record<string, string> = {
      ru: 'Russian',
      en: 'English',
      es: 'Spanish',
      fr: 'French',
      de: 'German',
    };
    const fullLang = langMap[targetLang] || targetLang;

    const livePrompts = readPrompts();
    let prompt =
      data.prompt ||
      (
        livePrompts.translate?.prompt ||
        this.configService.get<string>('gemini.translatePrompt') ||
        'Translate the following texts to {target_lang}. Return ONLY valid JSON with a "results" array.'
      ).replace('{target_lang}', fullLang);

    if (data.keep_memes) {
      const suffix =
        livePrompts.translate?.keep_memes_suffix ||
        this.configService.get<string>('gemini.keepMemesTranslateSuffix') ||
        ' IMPORTANT: If a line is a globally famous quote, meme, crowd noise, screaming, or a short untranslatable exclamation (e.g., "Ah shit", "Yo!", "Wow!", "Ahhh!"), DO NOT translate it. Leave it EXACTLY in its original English text.';
      prompt += suffix;
    }

    const texts = data.texts || [];
    this.logger.log(
      `Translating ${texts.length} phrases to "${fullLang}" (keep_memes=${!!data.keep_memes})`,
    );

    const candidateModels = Array.from(
      new Set([
        model,
        'gemini-3.5-flash',
        'gemini-3-flash-preview',
        'gemini-flash-latest',
        'gemini-3.6-flash',
      ]),
    );

    let response: Response | null = null;
    let lastErr = '';
    let usedModel = '';

    for (const curModel of candidateModels) {
      usedModel = curModel;
      const url = `${baseUrl.replace(/\/+$/, '')}/models/${curModel}:generateContent?key=${apiKey}`;
      try {
        response = await fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            systemInstruction: {
              parts: [{ text: prompt }],
            },
            contents: [
              {
                role: 'user',
                parts: [{ text: JSON.stringify(texts) }],
              },
            ],
            generationConfig: {
              temperature: data.temperature ?? 0.2,
              responseMimeType: 'application/json',
            },
          }),
        });

        if (response.ok) {
          break;
        }

        lastErr = await response.text();
        if (response.status === 503 || response.status === 429) {
          this.logger.warn(
            `Model ${curModel} returned ${response.status}. Trying next candidate model...`,
          );
          continue;
        }
        this.logger.error(
          `Model ${curModel} returned ${response.status}: ${lastErr.slice(0, 300)}`,
        );
        break;
      } catch (err: any) {
        lastErr = err.message || String(err);
        this.logger.warn(
          `Model ${curModel} fetch error: ${lastErr}. Trying next candidate...`,
        );
      }
    }

    if (!response || !response.ok) {
      this.logger.error(
        `All candidate models failed for translation: ${lastErr.slice(0, 500)}`,
      );
      throw new InternalServerErrorException(
        `Gemini Error (Translate): ${lastErr}`,
      );
    }

    const elapsed = Date.now() - startTime;
    const result = await response.json();
    const content = result.candidates?.[0]?.content?.parts?.[0]?.text;

    try {
      const parsed = JSON.parse(content);
      const out = Array.isArray(parsed.results)
        ? parsed.results
        : Array.isArray(parsed)
          ? parsed
          : parsed.results
            ? [parsed.results]
            : texts;
      this.logger.log(
        `Translation succeeded using ${usedModel} (${out.length} items) in ${elapsed}ms`,
      );
      return { results: out };
    } catch {
      this.logger.warn(
        `Failed to parse JSON response from ${usedModel}, returning original texts`,
      );
      return { results: texts };
    }
  }
}
