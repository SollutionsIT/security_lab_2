import { Module } from '@nestjs/common';
import { SSRF_ALLOWED_HOSTS, SsrfUrlPolicy } from '../ssrf/ssrf-url-policy';
import { AiParseController } from './ai-parse.controller';
import {
  AI_MODEL_GATEWAY,
  AiParseService,
  MockAiModelGateway,
} from './ai-parse.service';

@Module({
  controllers: [AiParseController],
  providers: [
    {
      provide: SSRF_ALLOWED_HOSTS,
      useFactory: (): readonly string[] =>
        (process.env.AI_SOURCE_ALLOWED_HOSTS ?? 'content.example.test')
          .split(',')
          .map((host) => host.trim())
          .filter(Boolean),
    },
    {
      provide: SsrfUrlPolicy,
      useFactory: (hosts: readonly string[]): SsrfUrlPolicy =>
        new SsrfUrlPolicy(hosts),
      inject: [SSRF_ALLOWED_HOSTS],
    },
    MockAiModelGateway,
    { provide: AI_MODEL_GATEWAY, useExisting: MockAiModelGateway },
    AiParseService,
  ],
  exports: [AiParseService, SsrfUrlPolicy],
})
export class AiParseModule {}
