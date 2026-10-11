import { InMemoryRepository } from './in-memory.repository';

describe('InMemoryRepository reset token expiry', () => {
  it('rejects and atomically removes an expired reset token', () => {
    const repository = new InMemoryRepository();
    repository.saveResetToken({
      tokenDigest: 'synthetic-digest',
      userId: 'user-alice',
      createdAt: 1_000,
      expiresAt: 2_000,
    });

    expect(repository.consumeValidResetToken('synthetic-digest', 2_001)).toBeUndefined();
    expect(repository.consumeValidResetToken('synthetic-digest', 1_500)).toBeUndefined();
  });
});
