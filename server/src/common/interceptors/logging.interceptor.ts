import {
  CallHandler,
  ExecutionContext,
  Injectable,
  Logger,
  NestInterceptor,
} from '@nestjs/common';
import type { Request, Response } from 'express';
import { Observable } from 'rxjs';
import { tap } from 'rxjs/operators';

@Injectable()
export class LoggingInterceptor implements NestInterceptor {
  private readonly logger = new Logger('HTTP');

  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    const ctx = context.switchToHttp();
    const req = ctx.getRequest<Request>();
    const res = ctx.getResponse<Response>();

    const { method, originalUrl, ip } = req;
    const startTime = Date.now();

    return next.handle().pipe(
      tap({
        next: () => {
          const duration = Date.now() - startTime;
          const statusCode = res.statusCode;
          const contentLength = res.get('content-length') || '-';

          const msg = `${method} ${originalUrl} ${statusCode} +${duration}ms [${ip}] len:${contentLength}`;
          if (statusCode >= 500) {
            this.logger.error(msg);
          } else if (statusCode >= 400) {
            this.logger.warn(msg);
          } else {
            this.logger.log(msg);
          }
        },
        error: (err) => {
          const duration = Date.now() - startTime;
          const statusCode = err.status || 500;
          this.logger.error(
            `${method} ${originalUrl} ${statusCode} +${duration}ms [${ip}] - ${err.message}`,
            err.stack,
          );
        },
      }),
    );
  }
}
