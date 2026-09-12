import { Controller, Post, Body, HttpCode } from '@nestjs/common';
import { TranslateService } from './translate.service.js';
@Controller('llm/translate')
export class TranslateController {
  constructor(private readonly translateService: TranslateService) {}
  @Post()
  @HttpCode(200)
  async translate(@Body() body: any) {
    return this.translateService.process(body);
  }
}
