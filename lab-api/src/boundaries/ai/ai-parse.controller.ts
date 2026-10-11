import { Body, Controller, Post, Req } from '@nestjs/common';
import {
  AllowedContentTypes,
  RateLimit,
} from '../../common/decorators/security.decorators';
import type { LabRequest } from '../../common/http/lab-request';
import { AiParseRequestDto } from './ai-parse.dto';
import { AiParseService } from './ai-parse.service';

@Controller('ai')
export class AiParseController {
  constructor(private readonly ai: AiParseService) {}

  @Post('parse')
  @RateLimit('ai_parse')
  @AllowedContentTypes('application/json')
  parse(@Body() body: AiParseRequestDto, @Req() request: LabRequest) {
    return this.ai.parse(
      body,
      request.actor?.id ?? 'anonymous',
      request.correlationId,
    );
  }
}
