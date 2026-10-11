import { Controller, Headers, HttpCode, HttpStatus, Post, Req } from '@nestjs/common';
import {
  AllowedContentTypes,
  Public,
} from '../../common/decorators/security.decorators';
import type { LabRequest } from '../../common/http/lab-request';
import { WebhookService } from './webhook.service';

interface RawBodyLabRequest extends LabRequest {
  rawBody?: Buffer;
}

@Controller('webhooks')
export class WebhookController {
  constructor(private readonly webhooks: WebhookService) {}

  @Post('stripe')
  @HttpCode(HttpStatus.OK)
  @Public()
  @AllowedContentTypes('application/json')
  handle(
    @Req() request: RawBodyLabRequest,
    @Headers('stripe-signature') signature: string | undefined,
  ) {
    return this.webhooks.handle(
      request.rawBody,
      signature,
      request.correlationId,
    );
  }
}
