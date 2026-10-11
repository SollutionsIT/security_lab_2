import { CanActivate, ExecutionContext, Inject, Injectable, NotFoundException } from '@nestjs/common';
import { createHash, timingSafeEqual } from 'node:crypto';
import { APP_CONFIG, AppConfig } from '../../config/app-config';
import type { LabRequest } from '../http/lab-request';

function digest(value: string): Buffer {
  return createHash('sha256').update(value, 'utf8').digest();
}

@Injectable()
export class TestOnlyGuard implements CanActivate {
  constructor(@Inject(APP_CONFIG) private readonly config: AppConfig) {}

  canActivate(context: ExecutionContext): boolean {
    if (!this.config.labTestMode || !this.config.labTestKey) {
      throw new NotFoundException();
    }
    const request = context.switchToHttp().getRequest<LabRequest>();
    const supplied = request.header('x-lab-test-key') ?? '';
    if (!timingSafeEqual(digest(supplied), digest(this.config.labTestKey))) {
      throw new NotFoundException();
    }
    return true;
  }
}
