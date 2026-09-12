import { Controller, Post, Body, HttpCode, Res } from '@nestjs/common';
import type { Response } from 'express';
import { TtsService } from './tts.service.js';

@Controller('llm/tts')
export class TtsController {
  constructor(private readonly ttsService: TtsService) {}

  @Post()
  @HttpCode(200)
  async tts(@Body() body: any, @Res() res: Response) {
    const stream = await this.ttsService.process(body);
    res.setHeader('Content-Type', 'audio/mpeg');
    res.setHeader('Transfer-Encoding', 'chunked');
    stream.pipe(res);
  }
}
