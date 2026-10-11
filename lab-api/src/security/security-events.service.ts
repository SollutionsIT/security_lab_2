import { Global, Injectable, Logger, Module } from '@nestjs/common';
import { redactSensitive } from './redaction';
import { RateLimiterService } from './rate-limiter.service';

export interface SecurityEventInput {
  readonly event: string;
  readonly actorId?: string;
  readonly resourceType?: string;
  readonly resourceId?: string;
  readonly action?: string;
  readonly result: 'allowed' | 'denied' | 'accepted' | 'failed';
  readonly correlationId: string;
  readonly reason?: string;
  readonly metadata?: Record<string, unknown>;
}

export interface SecurityEvent {
  readonly timestamp: string;
  readonly event: string;
  readonly actor_id?: string;
  readonly resource_type?: string;
  readonly resource_id?: string;
  readonly action?: string;
  readonly result: string;
  readonly correlation_id: string;
  readonly reason?: string;
  readonly metadata?: unknown;
}

@Injectable()
export class SecurityEventsService {
  private readonly logger = new Logger('SecurityEvent');
  private readonly events: SecurityEvent[] = [];

  record(input: SecurityEventInput): SecurityEvent {
    const event: SecurityEvent = {
      timestamp: new Date().toISOString(),
      event: String(redactSensitive(input.event)),
      ...(input.actorId ? { actor_id: String(redactSensitive(input.actorId)) } : {}),
      ...(input.resourceType
        ? { resource_type: String(redactSensitive(input.resourceType)) }
        : {}),
      ...(input.resourceId
        ? { resource_id: String(redactSensitive(input.resourceId)) }
        : {}),
      ...(input.action ? { action: String(redactSensitive(input.action)) } : {}),
      result: input.result,
      correlation_id: String(redactSensitive(input.correlationId)),
      ...(input.reason ? { reason: String(redactSensitive(input.reason)) } : {}),
      ...(input.metadata ? { metadata: redactSensitive(input.metadata) } : {}),
    };
    this.events.push(event);
    if (this.events.length > 1_000) this.events.shift();
    this.logger.log(JSON.stringify(event));
    return structuredClone(event);
  }

  list(): SecurityEvent[] {
    return structuredClone(this.events);
  }

  clear(): void {
    this.events.length = 0;
  }
}

@Global()
@Module({
  providers: [SecurityEventsService, RateLimiterService],
  exports: [SecurityEventsService, RateLimiterService],
})
export class SecurityModule {}
