import { Inject, Injectable, UnauthorizedException } from '@nestjs/common';
import { createHash, randomBytes } from 'node:crypto';
import { APP_CONFIG, AppConfig } from '../config/app-config';
import { InMemoryRepository } from '../data/in-memory.repository';
import { SecurityEventsService } from '../security/security-events.service';
import { TestMailboxService } from '../test-support/test-mailbox.service';
import {
  LoginDto,
  ResetPasswordConfirmDto,
  ResetPasswordRequestDto,
} from './auth.dto';
import { JwtTokenService } from './jwt-token.service';
import { createDeterministicSeedHash, PasswordService } from './password.service';

const GENERIC_LOGIN_ERROR = 'Invalid email or password';
const GENERIC_RESET_RESPONSE =
  'If the account exists, password reset instructions have been sent.';
const DUMMY_HASH = createDeterministicSeedHash(
  'Dummy-Local-Only!42',
  'dummy-seed-salt-04',
);

function digestToken(token: string): string {
  return createHash('sha256').update(token, 'utf8').digest('hex');
}

@Injectable()
export class AuthService {
  constructor(
    @Inject(APP_CONFIG) private readonly config: AppConfig,
    private readonly repository: InMemoryRepository,
    private readonly passwords: PasswordService,
    private readonly tokens: JwtTokenService,
    private readonly mailbox: TestMailboxService,
    private readonly securityEvents: SecurityEventsService,
  ) {}

  async login(dto: LoginDto, correlationId: string): Promise<Record<string, unknown>> {
    const user = this.repository.findUserByEmail(dto.email);
    const passwordValid = await this.passwords.verify(
      dto.password,
      user?.passwordHash ?? DUMMY_HASH,
    );
    if (!user || !passwordValid || !user.isVerified) {
      this.securityEvents.record({
        event: 'authentication_failed',
        actorId: 'anonymous',
        resourceType: 'session',
        action: 'login',
        result: 'failed',
        correlationId,
        reason: 'invalid_credentials',
      });
      throw new UnauthorizedException(GENERIC_LOGIN_ERROR);
    }
    const accessToken = await this.tokens.issue({ id: user.id, role: user.role });
    this.securityEvents.record({
      event: 'authentication_succeeded',
      actorId: user.id,
      resourceType: 'session',
      action: 'login',
      result: 'allowed',
      correlationId,
    });
    return {
      accessToken,
      tokenType: 'Bearer',
      expiresIn: this.config.jwt.ttlSeconds,
    };
  }

  requestReset(
    dto: ResetPasswordRequestDto,
    correlationId: string,
  ): { message: string } {
    const user = this.repository.findUserByEmail(dto.email);
    const token = randomBytes(32).toString('base64url');
    const tokenDigest = digestToken(token);
    const now = Date.now();
    if (user) {
      this.repository.deleteResetTokensForUser(user.id);
      this.repository.saveResetToken({
        tokenDigest,
        userId: user.id,
        createdAt: now,
        expiresAt: now + this.config.resetTokenTtlSeconds * 1_000,
      });
      this.mailbox.sendPasswordReset({
        kind: 'password_reset',
        recipient: user.email,
        resetToken: token,
        expiresAt: new Date(now + this.config.resetTokenTtlSeconds * 1_000).toISOString(),
      });
    }
    this.securityEvents.record({
      event: 'password_reset_requested',
      actorId: 'anonymous',
      resourceType: 'identity',
      action: 'request_reset',
      result: 'accepted',
      correlationId,
    });
    return { message: GENERIC_RESET_RESPONSE };
  }

  async confirmReset(
    dto: ResetPasswordConfirmDto,
    correlationId: string,
  ): Promise<{ message: string }> {
    const record = this.repository.consumeValidResetToken(
      digestToken(dto.token),
      Date.now(),
    );
    if (!record) {
      this.securityEvents.record({
        event: 'password_reset_failed',
        actorId: 'anonymous',
        resourceType: 'identity',
        action: 'confirm_reset',
        result: 'failed',
        correlationId,
        reason: 'invalid_or_expired',
      });
      throw new UnauthorizedException('Invalid or expired reset token');
    }
    const passwordHash = await this.passwords.hash(dto.newPassword);
    this.repository.updateUserPassword(record.userId, passwordHash);
    this.repository.deleteResetTokensForUser(record.userId);
    this.securityEvents.record({
      event: 'password_reset_completed',
      actorId: record.userId,
      resourceType: 'identity',
      action: 'confirm_reset',
      result: 'allowed',
      correlationId,
    });
    return { message: 'Password reset complete' };
  }
}
