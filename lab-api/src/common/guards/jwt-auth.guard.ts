import {
  CanActivate,
  ExecutionContext,
  Injectable,
  UnauthorizedException,
} from '@nestjs/common';
import { Reflector } from '@nestjs/core';
import { JwtTokenService } from '../../auth/jwt-token.service';
import { InMemoryRepository } from '../../data/in-memory.repository';
import { IS_PUBLIC_KEY } from '../decorators/security.decorators';
import type { LabRequest } from '../http/lab-request';

@Injectable()
export class JwtAuthGuard implements CanActivate {
  constructor(
    private readonly reflector: Reflector,
    private readonly tokens: JwtTokenService,
    private readonly repository: InMemoryRepository,
  ) {}

  async canActivate(context: ExecutionContext): Promise<boolean> {
    const isPublic = this.reflector.getAllAndOverride<boolean>(IS_PUBLIC_KEY, [
      context.getHandler(),
      context.getClass(),
    ]);
    if (isPublic) return true;

    const request = context.switchToHttp().getRequest<LabRequest>();
    const authorization = request.header('authorization');
    const match = /^Bearer ([^\s]+)$/.exec(authorization ?? '');
    if (!match?.[1]) throw new UnauthorizedException('Unauthorized');
    const actor = await this.tokens.verify(match[1]);
    const currentUser = this.repository.findUserById(actor.id);
    if (!currentUser || !currentUser.isVerified || currentUser.role !== actor.role) {
      throw new UnauthorizedException('Unauthorized');
    }
    request.actor = actor;
    return true;
  }
}
