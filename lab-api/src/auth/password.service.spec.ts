import { PasswordService } from './password.service';

describe('PasswordService', () => {
  const service = new PasswordService();

  it('stores a salted scrypt verifier rather than plaintext', async () => {
    const password = 'Synthetic-Only!42';
    const encoded = await service.hash(password);

    expect(encoded).toMatch(/^scrypt\$/);
    expect(encoded).not.toContain(password);
    await expect(service.verify(password, encoded)).resolves.toBe(true);
  });

  it('rejects the wrong password and malformed verifier', async () => {
    const encoded = await service.hash('Synthetic-Only!42');

    await expect(service.verify('Wrong-Only!42', encoded)).resolves.toBe(false);
    await expect(service.verify('Synthetic-Only!42', 'not-a-verifier')).resolves.toBe(
      false,
    );
  });
});
