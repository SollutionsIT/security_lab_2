import { SetMetadata } from '@nestjs/common';
import { Role } from '../../data/entities';

export const IS_PUBLIC_KEY = 'security:is-public';
export const Public = (): MethodDecorator & ClassDecorator =>
  SetMetadata(IS_PUBLIC_KEY, true);

export const ROLES_KEY = 'security:roles';
export const Roles = (...roles: Role[]): MethodDecorator & ClassDecorator =>
  SetMetadata(ROLES_KEY, roles);

export type RateLimitProfile = 'login' | 'reset' | 'public_form' | 'ai_parse';
export const RATE_LIMIT_KEY = 'security:rate-limit';
export const RateLimit = (profile: RateLimitProfile): MethodDecorator =>
  SetMetadata(RATE_LIMIT_KEY, profile);

export const CONTENT_TYPES_KEY = 'security:content-types';
export const AllowedContentTypes = (...mediaTypes: string[]): MethodDecorator =>
  SetMetadata(CONTENT_TYPES_KEY, mediaTypes);
