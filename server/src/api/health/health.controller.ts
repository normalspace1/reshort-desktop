import { Controller, Get, HttpCode } from '@nestjs/common';
import { HealthService } from './health.service.js';

@Controller('health')
export class HealthController {
  constructor(private readonly healthService: HealthService) {}

  @Get()
  @HttpCode(200)
  async check() {
    return this.healthService.checkServices();
  }
}
