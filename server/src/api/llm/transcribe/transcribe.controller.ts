import {
  Controller,
  Post,
  HttpCode,
  Req,
  UseInterceptors,
  UploadedFile,
  InternalServerErrorException,
} from '@nestjs/common';
import { FileInterceptor } from '@nestjs/platform-express';
import type { Request } from 'express';
import { TranscribeService } from './transcribe.service.js';

@Controller('llm/transcribe')
export class TranscribeController {
  constructor(private readonly transcribeService: TranscribeService) {}

  @Post()
  @HttpCode(200)
  @UseInterceptors(FileInterceptor('file'))
  async transcribe(@UploadedFile() file: any, @Req() req: Request) {
    if (!file) {
      throw new InternalServerErrorException('No audio file provided');
    }
    return this.transcribeService.process(file, (req.body as Record<string, any>) ?? {});
  }
}