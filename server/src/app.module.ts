import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';

import configuration from './common/config/configuration.js';

import { TranslateModule } from './api/llm/translate/translate.module.js';
import { AdaptModule } from './api/llm/adapt/adapt.module.js';
import { TranscribeModule } from './api/llm/transcribe/transcribe.module.js';
import { TtsModule } from './api/llm/tts/tts.module.js';
import { HealthModule } from './api/health/health.module.js';

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
      envFilePath: ['.env', 'server/.env'],
      load: [configuration],
    }),
    TranslateModule,
    AdaptModule,
    TranscribeModule,
    TtsModule,
    HealthModule,
  ],
})
export class AppModule {}
