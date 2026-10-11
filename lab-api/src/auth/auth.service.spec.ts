import { loadAppConfig } from '../config/app-config';
import { InMemoryRepository } from '../data/in-memory.repository';
import { SecurityEventsService } from '../security/security-events.service';
import { TestMailboxService } from '../test-support/test-mailbox.service';
import { AuthService } from './auth.service';
import { JwtTokenService } from './jwt-token.service';
import { PasswordService } from './password.service';

describe('AuthService reset expiry', () => {
  it('rejects an expired opaque reset token', async () => {
    const config = loadAppConfig({
      NODE_ENV: 'test',
      JWT_SECRET: 'synthetic-test-signing-key-at-least-32-characters',
      RESET_TOKEN_TTL_SECONDS: '60',
    });
    const repository = new InMemoryRepository();
    const mailbox = new TestMailboxService();
    const service = new AuthService(
      config,
      repository,
      new PasswordService(),
      new JwtTokenService(config),
      mailbox,
      new SecurityEventsService(),
    );
    const now = 1_800_000_000_000;
    const clock = jest.spyOn(Date, 'now').mockReturnValue(now);
    service.requestReset({ email: 'alice@example.test' }, 'correlation-request');
    const token = mailbox.list()[0]?.resetToken;
    expect(token).toBeDefined();

    clock.mockReturnValue(now + 60_001);
    await expect(
      service.confirmReset(
        { token: token!, newPassword: 'Replacement-Local!84' },
        'correlation-confirm',
      ),
    ).rejects.toThrow('Invalid or expired reset token');
    clock.mockRestore();
  });
});
