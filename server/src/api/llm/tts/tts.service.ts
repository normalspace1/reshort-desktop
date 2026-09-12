import { Injectable, InternalServerErrorException, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { Readable } from 'stream';

@Injectable()
export class TtsService {
  private readonly logger = new Logger(TtsService.name);

  constructor(private configService: ConfigService) {}

  async process(data: any): Promise<Readable> {
    const startTime = Date.now();
    const apiKey = this.configService.get<string>('fishAudio.apiKey');
    const url = this.configService.get<string>('fishAudio.apiUrl')!;

    if (!apiKey) {
      this.logger.error('FISH_AUDIO_API_KEY is missing in server configuration');
      throw new InternalServerErrorException(
        'FISH_AUDIO_API_KEY is not configured',
      );
    }

    const textSnippet = (data.text || '').slice(0, 50).replace(/\n/g, ' ');
    this.logger.log(
      `Synthesizing TTS via Fish Audio (${(data.text || '').length} chars): "${textSnippet}..."`,
    );

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${apiKey}`,
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const err = await response.text();
      this.logger.error(`Fish Audio TTS failed (${response.status}): ${err.slice(0, 300)}`);
      throw new InternalServerErrorException(`Fish Audio TTS Error: ${err}`);
    }

    const elapsed = Date.now() - startTime;
    this.logger.log(`Fish Audio TTS audio stream opened successfully in ${elapsed}ms`);

    return Readable.fromWeb(response.body as any);
  }
}
