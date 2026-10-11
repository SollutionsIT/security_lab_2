import { BadRequestException, UnauthorizedException } from '@nestjs/common';
import { createHmac } from 'node:crypto';
import type { SecurityEventsService } from '../../security/security-events.service';
import type {
  BoundInvoice,
  WebhookEventRecord,
  WebhookStateStore,
} from './webhook.service';
import { defaultWebhookConfig, WebhookService } from './webhook.service';

const SECRET = 'whsec_synthetic_unit_test_only_123456';
const NOW = 1_767_225_600;

class FakeWebhookState implements WebhookStateStore {
  invoice: BoundInvoice = {
    id: 'invoice-alice',
    orderId: 'order-alice',
    amountCents: 12_500,
    currency: 'EUR',
    state: 'open',
  };

  private readonly eventIds = new Set<string>();

  getInvoice(id: string): BoundInvoice | undefined {
    return id === this.invoice.id ? { ...this.invoice } : undefined;
  }

  claimEvent(event: WebhookEventRecord): boolean {
    if (this.eventIds.has(event.id)) return false;
    this.eventIds.add(event.id);
    return true;
  }

  markInvoicePaid(id: string): BoundInvoice {
    if (id !== this.invoice.id) throw new Error('unexpected invoice');
    this.invoice = { ...this.invoice, state: 'paid' };
    return { ...this.invoice };
  }
}

function signature(body: Buffer, timestamp = NOW): string {
  const digest = createHmac('sha256', SECRET)
    .update(`${timestamp}.`, 'utf8')
    .update(body)
    .digest('hex');
  return `t=${timestamp},v1=${digest}`;
}

function event(overrides: Record<string, unknown> = {}): Buffer {
  return Buffer.from(
    JSON.stringify({
      id: 'evt_synthetic_001',
      type: 'invoice.paid',
      created: NOW,
      data: {
        object: {
          invoiceId: 'invoice-alice',
          orderId: 'order-alice',
          amountCents: 12_500,
          currency: 'EUR',
        },
      },
      ...overrides,
    }),
  );
}

describe('WebhookService', () => {
  let state: FakeWebhookState;
  let service: WebhookService;

  beforeEach(() => {
    state = new FakeWebhookState();
    const events = { record: jest.fn() } as unknown as SecurityEventsService;
    service = new WebhookService({ signingSecret: SECRET }, state, events);
  });

  it('rejects a missing signature', () => {
    expect(() => service.handle(event(), undefined, 'correlation-1234', NOW)).toThrow(
      UnauthorizedException,
    );
  });

  it('rejects an invalid signature', () => {
    expect(() =>
      service.handle(event(), `t=${NOW},v1=${'00'.repeat(32)}`, 'correlation-1234', NOW),
    ).toThrow(UnauthorizedException);
  });

  it('processes a valid event using server-bound invoice values', () => {
    const body = event();
    expect(service.handle(body, signature(body), 'correlation-1234', NOW)).toEqual({
      status: 'processed',
      eventId: 'evt_synthetic_001',
      invoiceId: 'invoice-alice',
      invoiceState: 'paid',
    });
    expect(state.invoice.state).toBe('paid');
  });

  it('treats an already claimed event as a duplicate', () => {
    const body = event();
    service.handle(body, signature(body), 'correlation-1234', NOW);
    expect(service.handle(body, signature(body), 'correlation-1234', NOW)).toEqual({
      status: 'duplicate',
      eventId: 'evt_synthetic_001',
    });
  });

  it('rejects an old or replayed signed timestamp', () => {
    const body = event({ created: NOW - 301 });
    expect(() =>
      service.handle(body, signature(body, NOW - 301), 'correlation-1234', NOW),
    ).toThrow(UnauthorizedException);
  });

  it('accepts but ignores an unknown event type', () => {
    const body = event({ type: 'synthetic.unknown' });
    expect(service.handle(body, signature(body), 'correlation-1234', NOW)).toEqual({
      status: 'ignored',
      eventId: 'evt_synthetic_001',
    });
    expect(state.invoice.state).toBe('open');
  });

  it('rejects a body modified after signing', () => {
    const original = event();
    const modified = event({ id: 'evt_modified' });
    expect(() =>
      service.handle(modified, signature(original), 'correlation-1234', NOW),
    ).toThrow(UnauthorizedException);
  });

  it('rejects amount/order/resource substitution', () => {
    const body = event({
      data: {
        object: {
          invoiceId: 'invoice-alice',
          orderId: 'order-attacker',
          amountCents: 1,
          currency: 'EUR',
        },
      },
    });
    expect(() =>
      service.handle(body, signature(body), 'correlation-1234', NOW),
    ).toThrow(BadRequestException);
    expect(state.invoice.state).toBe('open');
  });
});

describe('defaultWebhookConfig', () => {
  it('fails closed on a missing production webhook secret', () => {
    const previousEnvironment = process.env.NODE_ENV;
    const previousSecret = process.env.SYNTHETIC_WEBHOOK_SECRET;
    process.env.NODE_ENV = 'production';
    delete process.env.SYNTHETIC_WEBHOOK_SECRET;
    try {
      expect(() => defaultWebhookConfig()).toThrow(
        'SYNTHETIC_WEBHOOK_SECRET must be an explicit non-placeholder value in production',
      );
    } finally {
      if (previousEnvironment === undefined) delete process.env.NODE_ENV;
      else process.env.NODE_ENV = previousEnvironment;
      if (previousSecret === undefined) delete process.env.SYNTHETIC_WEBHOOK_SECRET;
      else process.env.SYNTHETIC_WEBHOOK_SECRET = previousSecret;
    }
  });
});
