import { BadRequestException, Injectable } from '@nestjs/common';
import { isIP } from 'node:net';

export const SSRF_ALLOWED_HOSTS = Symbol('SSRF_ALLOWED_HOSTS');

export const SSRF_REQUEST_BUDGET = Object.freeze({
  redirects: 0,
  timeoutMs: 2_000,
  maxResponseBytes: 262_144,
});

export interface ValidatedOutboundRequest {
  readonly url: URL;
  readonly redirect: 'error';
  readonly timeoutMs: number;
  readonly maxResponseBytes: number;
}

function normalizeAddress(value: string): string {
  const withoutBrackets = value.startsWith('[') && value.endsWith(']')
    ? value.slice(1, -1)
    : value;
  const zoneIndex = withoutBrackets.indexOf('%');
  return (zoneIndex === -1
    ? withoutBrackets
    : withoutBrackets.slice(0, zoneIndex)
  ).toLowerCase();
}

function isBlockedIpv4(address: string): boolean {
  const octets = address.split('.').map(Number);
  if (
    octets.length !== 4 ||
    octets.some((octet) => !Number.isInteger(octet) || octet < 0 || octet > 255)
  ) {
    return true;
  }

  const [a = 0, b = 0] = octets;
  return (
    a === 0 ||
    a === 10 ||
    a === 127 ||
    (a === 100 && b >= 64 && b <= 127) ||
    (a === 169 && b === 254) ||
    (a === 172 && b >= 16 && b <= 31) ||
    (a === 192 && (b === 0 || b === 168)) ||
    (a === 198 && (b === 18 || b === 19 || b === 51)) ||
    (a === 203 && b === 0) ||
    a >= 224
  );
}

function isBlockedIpv6(address: string): boolean {
  if (address === '::' || address === '::1') {
    return true;
  }

  const mappedIpv4 = /(?:^|:)ffff:(\d+\.\d+\.\d+\.\d+)$/.exec(address)?.[1];
  if (mappedIpv4) {
    return isBlockedIpv4(mappedIpv4);
  }
  if (address.startsWith('::ffff:')) {
    return true;
  }

  const firstHextetText = address.split(':')[0] ?? '';
  const firstHextet = Number.parseInt(firstHextetText || '0', 16);
  return (
    (firstHextet & 0xfe00) === 0xfc00 ||
    (firstHextet & 0xffc0) === 0xfe80 ||
    (firstHextet & 0xff00) === 0xff00 ||
    address.startsWith('2001:db8:')
  );
}

export function isPublicIpAddress(value: string): boolean {
  const address = normalizeAddress(value);
  const family = isIP(address);
  if (family === 4) {
    return !isBlockedIpv4(address);
  }
  if (family === 6) {
    return !isBlockedIpv6(address);
  }
  return false;
}

@Injectable()
export class SsrfUrlPolicy {
  private readonly allowedHosts: ReadonlySet<string>;

  constructor(allowedHosts: readonly string[]) {
    this.allowedHosts = new Set(
      allowedHosts.map((host) => host.trim().toLowerCase()).filter(Boolean),
    );
  }

  validate(rawUrl: string): ValidatedOutboundRequest {
    let url: URL;
    try {
      url = new URL(rawUrl);
    } catch {
      throw new BadRequestException('Source URL is invalid');
    }

    if (url.protocol !== 'https:') {
      throw new BadRequestException('Only HTTPS source URLs are allowed');
    }
    if (url.username || url.password) {
      throw new BadRequestException('URL credentials are not allowed');
    }
    if (url.port && url.port !== '443') {
      throw new BadRequestException('Non-default ports are not allowed');
    }
    if (url.hash) {
      throw new BadRequestException('URL fragments are not allowed');
    }

    const hostname = normalizeAddress(url.hostname);
    if (
      isIP(hostname) !== 0 ||
      hostname === 'localhost' ||
      hostname.endsWith('.localhost') ||
      hostname.endsWith('.local') ||
      hostname.endsWith('.internal')
    ) {
      throw new BadRequestException('IP and local source hosts are not allowed');
    }
    if (!this.allowedHosts.has(hostname)) {
      throw new BadRequestException('Source host is not allowlisted');
    }

    return Object.freeze({
      url,
      redirect: 'error' as const,
      timeoutMs: SSRF_REQUEST_BUDGET.timeoutMs,
      maxResponseBytes: SSRF_REQUEST_BUDGET.maxResponseBytes,
    });
  }

  /**
   * Call this on every address returned by a trusted resolver immediately before
   * connecting. A real transport must pin that validated address to avoid DNS
   * rebinding. This lab intentionally contains no HTTP client or fetch call.
   */
  assertResolvedAddresses(addresses: readonly string[]): void {
    if (addresses.length === 0 || addresses.some((address) => !isPublicIpAddress(address))) {
      throw new BadRequestException('Source host resolved to a non-public address');
    }
  }
}
