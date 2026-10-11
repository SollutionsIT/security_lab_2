import { INestApplication, ValidationPipe } from '@nestjs/common';
import { json, Request, text } from 'express';
import helmet from 'helmet';
import { APP_CONFIG, AppConfig } from './config/app-config';
import { correlationIdMiddleware } from './common/http/correlation-id';

export function configureApplication(app: INestApplication): void {
  const config = app.get<AppConfig>(APP_CONFIG);
  app.use(helmet());
  app.use(correlationIdMiddleware);
  app.use(
    json({
      limit: config.jsonBodyLimitBytes,
      type: ['application/json', 'application/*+json'],
      verify: (request, _response, buffer): void => {
        (request as Request & { rawBody?: Buffer }).rawBody = Buffer.from(buffer);
      },
    }),
  );
  app.use(
    text({
      limit: '32kb',
      type: ['application/xml', 'text/xml'],
    }),
  );
  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,
      transform: true,
      forbidNonWhitelisted: true,
    }),
  );
  app.enableShutdownHooks();
}
