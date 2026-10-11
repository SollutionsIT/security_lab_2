import 'reflect-metadata';
import { Logger } from '@nestjs/common';
import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';
import { configureApplication } from './bootstrap';
import { APP_CONFIG, AppConfig } from './config/app-config';

async function bootstrap(): Promise<void> {
  const app = await NestFactory.create(AppModule, { bodyParser: false });
  configureApplication(app);
  const config = app.get<AppConfig>(APP_CONFIG);
  await app.listen(config.port, config.host);
  Logger.log(`Synthetic lab listening on http://${config.host}:${config.port}`, 'Bootstrap');
}

void bootstrap();
