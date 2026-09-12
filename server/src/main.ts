import { NestFactory } from '@nestjs/core';
import { Logger } from '@nestjs/common';
import { DocumentBuilder, SwaggerModule } from '@nestjs/swagger';
import express from 'express';
import { AppModule } from './app.module.js';
import { LoggingInterceptor } from './common/interceptors/logging.interceptor.js';
import { AllExceptionsFilter } from './common/filters/http-exception.filter.js';

async function bootstrap() {
  const logger = new Logger('Bootstrap');
  const app = await NestFactory.create(AppModule, {
    bodyParser: false,
    logger: ['error', 'warn', 'log', 'debug', 'verbose'],
  });

  app.use(express.json({ limit: '100mb' }));
  app.use(express.urlencoded({ extended: true, limit: '100mb' }));
  app.enableCors();
  app.enableShutdownHooks();

  app.useGlobalInterceptors(new LoggingInterceptor());
  app.useGlobalFilters(new AllExceptionsFilter());

  const swaggerConfig = new DocumentBuilder()
    .setTitle('Revoice AI API')
    .setDescription(
      'Production AI services for automatic video translation, script adaptation, transcription, and TTS dubbing.',
    )
    .setVersion('1.0')
    .addTag('llm', 'LLM generation & translation endpoints')
    .addTag('health', 'System health checks')
    .build();
  const swaggerDoc = SwaggerModule.createDocument(app, swaggerConfig);
  SwaggerModule.setup('api/docs', app, swaggerDoc);

  const port = process.env.PORT || 3000;
  await app.listen(port);

  logger.log(`==============================================`);
  logger.log(` Revoice AI Server started on port ${port}`);
  logger.log(` Swagger Docs:  GET  http://localhost:${port}/api/docs`);
  logger.log(` Health check:  GET  http://localhost:${port}/health`);
  logger.log(` Translate:     POST http://localhost:${port}/llm/translate`);
  logger.log(` Adapt script:  POST http://localhost:${port}/llm/adapt`);
  logger.log(` Transcribe:    POST http://localhost:${port}/llm/transcribe`);
  logger.log(` TTS Dubbing:   POST http://localhost:${port}/llm/tts`);
  logger.log(` Prompts file:  server/prompts.json (live reload)`);
  logger.log(`==============================================`);
}
bootstrap();
