import { SignJWT } from 'jose';
import { loadAppConfig } from '../config/app-config';
import { Role } from '../data/entities';
import { JwtTokenService } from './jwt-token.service';

describe('JwtTokenService', () => {
  const config = loadAppConfig({
    NODE_ENV: 'test',
    JWT_SECRET: 'synthetic-test-signing-key-at-least-32-characters',
    JWT_ISSUER: 'test-issuer',
    JWT_AUDIENCE: 'test-audience',
  });
  const service = new JwtTokenService(config);

  it('round-trips an HS256 token with exact claims', async () => {
    const token = await service.issue({ id: 'user-alice', role: Role.User });
    await expect(service.verify(token)).resolves.toEqual({
      id: 'user-alice',
      role: Role.User,
    });
  });

  it('rejects a token signed with a non-allowlisted algorithm', async () => {
    const token = await new SignJWT({ role: Role.User })
      .setProtectedHeader({ alg: 'HS384', typ: 'JWT' })
      .setSubject('user-alice')
      .setIssuer(config.jwt.issuer)
      .setAudience(config.jwt.audience)
      .setIssuedAt()
      .setExpirationTime('5m')
      .sign(new TextEncoder().encode(config.jwt.secret));

    await expect(service.verify(token)).rejects.toThrow('Unauthorized');
  });

  it.each([
    ['wrong issuer', 'other-issuer', config.jwt.audience, '5m'],
    ['wrong audience', config.jwt.issuer, 'other-audience', '5m'],
    ['expired token', config.jwt.issuer, config.jwt.audience, '-1m'],
  ])('rejects %s', async (_label, issuer, audience, expiration) => {
    const token = await new SignJWT({ role: Role.User })
      .setProtectedHeader({ alg: 'HS256', typ: 'JWT' })
      .setSubject('user-alice')
      .setIssuer(issuer)
      .setAudience(audience)
      .setIssuedAt()
      .setExpirationTime(expiration)
      .sign(new TextEncoder().encode(config.jwt.secret));

    await expect(service.verify(token)).rejects.toThrow('Unauthorized');
  });
});
