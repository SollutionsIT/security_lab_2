import { Module } from '@nestjs/common';
import { RepositoryWebhookStateStore } from './repository-webhook-state.store';
import { WebhookController } from './webhook.controller';
import {
  defaultWebhookConfig,
  WEBHOOK_CONFIG,
  WEBHOOK_STATE_STORE,
  WebhookService,
} from './webhook.service';

@Module({
  controllers: [WebhookController],
  providers: [
    { provide: WEBHOOK_CONFIG, useFactory: defaultWebhookConfig },
    RepositoryWebhookStateStore,
    { provide: WEBHOOK_STATE_STORE, useExisting: RepositoryWebhookStateStore },
    WebhookService,
  ],
  exports: [WebhookService, WEBHOOK_STATE_STORE],
})
export class WebhookModule {}
