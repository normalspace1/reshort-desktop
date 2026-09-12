import { Injectable, InternalServerErrorException, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';

@Injectable()
export class TranscribeService {
  private readonly logger = new Logger(TranscribeService.name);

  constructor(private configService: ConfigService) {}

  async process(file: any, body: Record<string, any>) {
    const startTime = Date.now();
    const apiKey = this.configService.get<string>('groq.apiKey');
    const url = this.configService.get<string>('groq.apiUrl')!;
    const model = body.model || this.configService.get<string>('groq.model')!;

    if (!apiKey) {
      this.logger.error('GROQ_API_KEY is missing in server configuration');
      throw new InternalServerErrorException('GROQ_API_KEY is not configured');
    }

    const sizeMb = (file.size / (1024 * 1024)).toFixed(2);
    this.logger.log(
      `Starting transcription with model="${model}" for file="${file.originalname || 'audio.wav'}" (${sizeMb} MB)`,
    );

    const formData = new FormData();
    formData.append('file', new Blob([file.buffer]), file.originalname || 'audio.wav');
    formData.append('model', model);
    formData.append('response_format', body.response_format || 'verbose_json');
    if (body['timestamp_granularities[]'])
      formData.append('timestamp_granularities[]', body['timestamp_granularities[]']);
    if (body.temperature !== undefined && body.temperature !== '')
      formData.append('temperature', String(body.temperature));
    if (body.language) formData.append('language', body.language);

    const response = await fetch(url, {
      method: 'POST',
      headers: { Authorization: `Bearer ${apiKey}` },
      body: formData,
    });

    if (!response.ok) {
      const err = await response.text();
      this.logger.error(`Groq Whisper transcription failed (${response.status}): ${err.slice(0, 400)}`);
      throw new InternalServerErrorException(`Groq Whisper Error: ${err}`);
    }

    const elapsed = Date.now() - startTime;
    const result = await response.json();
    const segCount = result.segments?.length ?? 0;
    const wordsCount = result.words?.length ?? 0;

    this.logger.log(
      `Transcription completed in ${elapsed}ms: lang="${result.language}", duration=${result.duration}s, segments=${segCount}, words=${wordsCount}`,
    );

    return {
      text: result.text ?? '',
      language: result.language ?? null,
      duration: result.duration ?? null,
      segments: result.segments ?? [],
      words: result.words ?? [],
    };
  }
}