import {
  CanActivate,
  ExecutionContext,
  Injectable,
  UnsupportedMediaTypeException,
} from '@nestjs/common';
import { Reflector } from '@nestjs/core';
import type { Request } from 'express';
import { CONTENT_TYPES_KEY } from '../decorators/security.decorators';

@Injectable()
export class ContentTypeGuard implements CanActivate {
  constructor(private readonly reflector: Reflector) {}

  canActivate(context: ExecutionContext): boolean {
    const request = context.switchToHttp().getRequest<Request>();
    if (!['POST', 'PUT', 'PATCH'].includes(request.method)) return true;

    const explicit = this.reflector.getAllAndOverride<string[] | undefined>(
      CONTENT_TYPES_KEY,
      [context.getHandler(), context.getClass()],
    );
    if (explicit?.length === 0) return true;
    const allowed = explicit ?? ['application/json'];
    const mediaType = request.headers['content-type']?.split(';', 1)[0]?.trim().toLowerCase();
    if (!mediaType || !allowed.includes(mediaType)) {
      throw new UnsupportedMediaTypeException('Unsupported content type');
    }
    return true;
  }
}
