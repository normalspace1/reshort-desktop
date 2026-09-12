import { Injectable, InternalServerErrorException, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { readPrompts } from '../../../common/config/configuration.js';

@Injectable()
export class AdaptService {
  private readonly logger = new Logger(AdaptService.name);

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

    const livePrompts = readPrompts();
    let basePrompt =
      data.prompt ||
      livePrompts.adapt?.prompt ||
      this.configService.get<string>('gemini.adaptPrompt') ||
      'Rewrite each line for a Russian TTS dubbing script. Keep natural flow, match timing and emotion.';

    if (data.keep_memes) {
      const suffix =
        livePrompts.adapt?.keep_memes_suffix ||
        this.configService.get<string>('gemini.keepMemesAdaptSuffix') ||
        ' If a line is an English meme/quote (e.g. "Ah shit, here we go again"), leave it EXACTLY in English, do not translate or transliterate it. For all other lines, keep them in Russian.';
      basePrompt += suffix;
    }

    const prompt =
      basePrompt +
      "\nReturn ONLY valid JSON with a 'results' array containing the adapted strings in the exact same order.";
    const texts = data.texts || [];
    this.logger.log(
      `Adapting ${texts.length} phrases for TTS (keep_memes=${!!data.keep_memes})`,
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
        `All candidate models failed for adapt: ${lastErr.slice(0, 500)}`,
      );
      throw new InternalServerErrorException(`Gemini Error (Adapt): ${lastErr}`);
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
        `Script adaptation succeeded using ${usedModel} (${out.length} items) in ${elapsed}ms`,
      );
      return { results: out };
    } catch {
      const lines = (content || '')
        .split('\n')
        .map((l: string) => l.replace(/^\d+[\.\)]\s*/, '').trim())
        .filter(Boolean);
      const out = lines.length > 0 ? lines : texts;
      this.logger.log(
        `Script adaptation parsed fallback lines using ${usedModel} (${out.length} items) in ${elapsed}ms`,
      );
      return { results: out };
    }
  }
}
