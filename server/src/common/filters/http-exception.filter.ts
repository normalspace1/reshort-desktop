import {
  ArgumentsHost,
  Catch,
  ExceptionFilter,
  HttpException,
  HttpStatus,
  Logger,
} from '@nestjs/common';
import type { Request, Response } from 'express';

@Catch()
export class AllExceptionsFilter implements ExceptionFilter {
  private readonly logger = new Logger('Exceptions');

  catch(exception: unknown, host: ArgumentsHost) {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse<Response>();
    const request = ctx.getRequest<Request>();

    const status =
      exception instanceof HttpException
        ? exception.getStatus()
        : HttpStatus.INTERNAL_SERVER_ERROR;

    const message =
      exception instanceof HttpException
        ? exception.getResponse()
        : (exception as Error)?.message || 'Internal server error';

    const normalizedMessage =
      typeof message === 'object' && message !== null
        ? (message as any).message || message
        : message;

    this.logger.error(
      `Unhandled error at [${request.method} ${request.url}] Status: ${status} - ${JSON.stringify(normalizedMessage)}`,
      (exception as Error)?.stack,
    );

    response.status(status).json({
      statusCode: status,
      timestamp: new Date().toISOString(),
      path: request.url,
      method: request.method,
      message: normalizedMessage,
      error:
        exception instanceof HttpException
          ? exception.name
          : 'InternalServerError',
    });
  }
}
