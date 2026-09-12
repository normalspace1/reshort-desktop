import { Controller, Post, Body, HttpCode } from '@nestjs/common';
import { AdaptService } from './adapt.service.js';
@Controller('llm/adapt')
export class AdaptController {
  constructor(private readonly adaptService: AdaptService) {}
  @Post()
  @HttpCode(200)
  async adapt(@Body() body: any) {
    return this.adaptService.process(body);
  }
}
