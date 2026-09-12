import { Module } from '@nestjs/common';
import { AdaptController } from './adapt.controller.js';
import { AdaptService } from './adapt.service.js';
@Module({
  controllers: [AdaptController],
  providers: [AdaptService],
})
export class AdaptModule {}
