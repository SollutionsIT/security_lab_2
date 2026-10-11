import {
  CanActivate,
  ExecutionContext,
  HttpException,
  HttpStatus,
  Injectable,
} from '@nestjs/common';
import { Reflector } from '@nestjs/core';
import type { Response } from 'express';
import { RATE_LIMIT_KEY, RateLimitProfile } from '../decorators/security.decorators';
import type { LabRequest } from '../http/lab-request';
import { RateLimiterService } from '../../security/rate-limiter.service';
import { SecurityEventsService } from '../../security/security-events.service';

@Injectable()
export class RateLimitGuard implements CanActivate {
  constructor(
    private readonly reflector: Reflector,
    private readonly limiter: RateLimiterService,
    private readonly securityEvents: SecurityEventsService,
  ) {}

  canActivate(context: ExecutionContext): boolean {
    const profile = this.reflector.getAllAndOverride<RateLimitProfile | undefined>(
      RATE_LIMIT_KEY,
      [context.getHandler(), context.getClass()],
    );
    if (!profile) return true;

    const request = context.switchToHttp().getRequest<LabRequest>();
    const response = context.switchToHttp().getResponse<Response>();
    const body = request.body as Record<string, unknown> | undefined;
    const subject = typeof body?.email === 'string' ? body.email : undefined;
    const decision = this.limiter.check(profile, request.ip ?? 'unknown', subject);
    response.setHeader('x-ratelimit-limit', decision.limit);
    response.setHeader('x-ratelimit-remaining', decision.remaining);
    if (!decision.allowed) {
      response.setHeader('retry-after', decision.retryAfterSeconds);
      this.securityEvents.record({
        event: 'rate_limit_exceeded',
        actorId: request.actor?.id ?? 'anonymous',
        resourceType: 'route',
        resourceId: profile,
        action: request.method.toLowerCase(),
        result: 'denied',
        correlationId: request.correlationId,
        reason: 'deterministic_threshold',
      });
      throw new HttpException('Too many requests', HttpStatus.TOO_MANY_REQUESTS);
    }
    return true;
  }
}
