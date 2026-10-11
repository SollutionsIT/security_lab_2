import { loadAppConfig } from './app-config';

describe('loadAppConfig', () => {
  it('uses loopback and permits the documented placeholder in development', () => {
    const config = loadAppConfig({
      NODE_ENV: 'development',
      JWT_SECRET: 'replace-me',
    });

    expect(config.host).toBe('127.0.0.1');
    expect(config.jwt.secret).toBe('replace-me');
    expect(config.labTestMode).toBe(false);
  });

  it.each(['replace-me', 'change-me-now', 'short'])(
    'fails closed for a weak or placeholder production JWT secret: %s',
    (jwtSecret) => {
      expect(() =>
        loadAppConfig({ NODE_ENV: 'production', JWT_SECRET: jwtSecret }),
      ).toThrow(/JWT_SECRET/);
    },
  );

  it('rejects test-only support in production', () => {
    expect(() =>
      loadAppConfig({
        NODE_ENV: 'production',
        JWT_SECRET: 'a-production-shaped-synthetic-value-123456789',
        LAB_TEST_MODE: 'true',
        LAB_TEST_KEY: 'local-test-key-long-enough',
      }),
    ).toThrow(/LAB_TEST_MODE/);
  });

  it('requires an adequately bounded key when test support is enabled', () => {
    expect(() =>
      loadAppConfig({
        NODE_ENV: 'test',
        JWT_SECRET: 'test-signing-value-at-least-32-characters',
        LAB_TEST_MODE: 'true',
        LAB_TEST_KEY: 'short',
      }),
    ).toThrow(/LAB_TEST_KEY/);
  });
});
