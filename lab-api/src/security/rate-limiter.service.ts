import { Injectable } from '@nestjs/common';
import { createHash } from 'node:crypto';
import type { RateLimitProfile } from '../common/decorators/security.decorators';

const POLICIES: Readonly<Record<RateLimitProfile, { limit: number; windowMs: number }>> =
  Object.freeze({
    login: { limit: 5, windowMs: 60_000 },
    reset: { limit: 3, windowMs: 60_000 },
    public_form: { limit: 4, windowMs: 60_000 },
    ai_parse: { limit: 2, windowMs: 60_000 },
  });

interface Bucket {
  count: number;
  resetAt: number;
}

export interface RateLimitDecision {
  readonly allowed: boolean;
  readonly limit: number;
  readonly remaining: number;
  readonly retryAfterSeconds: number;
}

@Injectable()
export class RateLimiterService {
  private readonly buckets = new Map<string, Bucket>();

  check(profile: RateLimitProfile, source: string, subject?: string): RateLimitDecision {
    const policy = POLICIES[profile];
    const now = Date.now();
    this.prune(now);
    const keys = [`${profile}:source:${source}`];
    if (subject) {
      const digest = createHash('sha256').update(subject.toLowerCase()).digest('hex');
      keys.push(`${profile}:subject:${digest}`);
    }

    const buckets = keys.map((key) => this.getBucket(key, now, policy.windowMs));
    const denied = buckets.find((bucket) => bucket.count >= policy.limit);
    if (denied) {
      return {
        allowed: false,
        limit: policy.limit,
        remaining: 0,
        retryAfterSeconds: Math.max(1, Math.ceil((denied.resetAt - now) / 1_000)),
      };
    }
    for (const bucket of buckets) bucket.count += 1;
    const maximumCount = Math.max(...buckets.map((bucket) => bucket.count));
    return {
      allowed: true,
      limit: policy.limit,
      remaining: Math.max(0, policy.limit - maximumCount),
      retryAfterSeconds: 0,
    };
  }

  clear(): void {
    this.buckets.clear();
  }

  private getBucket(key: string, now: number, windowMs: number): Bucket {
    const existing = this.buckets.get(key);
    if (existing && existing.resetAt > now) return existing;
    const bucket = { count: 0, resetAt: now + windowMs };
    this.buckets.set(key, bucket);
    return bucket;
  }

  private prune(now: number): void {
    for (const [key, bucket] of this.buckets.entries()) {
      if (bucket.resetAt <= now) this.buckets.delete(key);
    }
    if (this.buckets.size > 10_000) this.buckets.clear();
  }
}
