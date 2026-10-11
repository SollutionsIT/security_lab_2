import { CanActivate, ExecutionContext, ForbiddenException, Injectable } from '@nestjs/common';
import { Reflector } from '@nestjs/core';
import { Role } from '../../data/entities';
import { SecurityEventsService } from '../../security/security-events.service';
import { ROLES_KEY } from '../decorators/security.decorators';
import type { LabRequest } from '../http/lab-request';

@Injectable()
export class RolesGuard implements CanActivate {
  constructor(
    private readonly reflector: Reflector,
    private readonly securityEvents: SecurityEventsService,
  ) {}

  canActivate(context: ExecutionContext): boolean {
    const roles = this.reflector.getAllAndOverride<Role[] | undefined>(ROLES_KEY, [
      context.getHandler(),
      context.getClass(),
    ]);
    if (!roles?.length) return true;
    const request = context.switchToHttp().getRequest<LabRequest>();
    if (request.actor && roles.includes(request.actor.role)) return true;

    this.securityEvents.record({
      event: 'authorization_denied',
      actorId: request.actor?.id ?? 'anonymous',
      resourceType: 'admin_function',
      resourceId: 'audit-events',
      action: request.method.toLowerCase(),
      result: 'denied',
      correlationId: request.correlationId,
      reason: 'insufficient_role',
    });
    throw new ForbiddenException('Forbidden');
  }
}
