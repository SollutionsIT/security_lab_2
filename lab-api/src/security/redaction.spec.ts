import { redactSensitive } from './redaction';

describe('redactSensitive', () => {
  it('removes secret fields, PII, bearer values, JWT-like strings, and log controls', () => {
    const sentinel = 'secret-sentinel-value';
    const result = redactSensitive({
      password: sentinel,
      authorization: `Bearer ${sentinel}`,
      resetToken: sentinel,
      email: 'person@example.test',
      note: 'safe\nline eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.signature',
    });
    const serialized = JSON.stringify(result);

    expect(serialized).not.toContain(sentinel);
    expect(serialized).not.toContain('person@example.test');
    expect(serialized).not.toContain('eyJhbGci');
    expect(serialized).not.toContain('\\n');
    expect(serialized).toContain('[REDACTED]');
  });
});
