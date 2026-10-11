import { BadRequestException } from '@nestjs/common';
import {
  SSRF_REQUEST_BUDGET,
  SsrfUrlPolicy,
  isPublicIpAddress,
} from './ssrf-url-policy';

describe('SsrfUrlPolicy', () => {
  const policy = new SsrfUrlPolicy(['imports.example.test']);

  it('allows an exact HTTPS allowlisted host with fixed budgets', () => {
    const result = policy.validate('https://imports.example.test/feed.xml?limit=10');

    expect(result.url.hostname).toBe('imports.example.test');
    expect(result.redirect).toBe('error');
    expect(result.timeoutMs).toBe(SSRF_REQUEST_BUDGET.timeoutMs);
    expect(result.maxResponseBytes).toBe(SSRF_REQUEST_BUDGET.maxResponseBytes);
  });

  it.each([
    'http://imports.example.test/feed.xml',
    'https://imports.example.test.evil.invalid/feed.xml',
    'https://sub.imports.example.test/feed.xml',
    'https://user:password@imports.example.test/feed.xml',
    'https://imports.example.test:8443/feed.xml',
    'https://imports.example.test/feed.xml#fragment',
    'https://127.0.0.1/feed.xml',
    'https://[::1]/feed.xml',
    'https://169.254.169.254/latest/meta-data',
  ])('rejects unsafe URL %s', (candidate) => {
    expect(() => policy.validate(candidate)).toThrow(BadRequestException);
  });

  it.each([
    '10.0.0.1',
    '127.0.0.1',
    '169.254.169.254',
    '172.16.0.1',
    '192.168.1.1',
    '::1',
    'fe80::1',
    'fd00::1',
    '::ffff:127.0.0.1',
  ])('rejects non-public resolved address %s', (address) => {
    expect(isPublicIpAddress(address)).toBe(false);
    expect(() => policy.assertResolvedAddresses([address])).toThrow(
      BadRequestException,
    );
  });

  it('accepts only non-empty sets of public resolved addresses', () => {
    expect(() => policy.assertResolvedAddresses([])).toThrow(BadRequestException);
    expect(() => policy.assertResolvedAddresses(['93.184.216.34'])).not.toThrow();
  });
});
