import {
  BadRequestException,
  Inject,
  Injectable,
  UnauthorizedException,
} from '@nestjs/common';
import { createHmac, timingSafeEqual } from 'node:crypto';
import { SecurityEventsService } from '../../security/security-events.service';

export const WEBHOOK_CONFIG = Symbol('WEBHOOK_CONFIG');
export const WEBHOOK_STATE_STORE = Symbol('WEBHOOK_STATE_STORE');
export const WEBHOOK_TIMESTAMP_TOLERANCE_SECONDS = 300;
const MAX_WEBHOOK_BYTES = 32_768;

export interface WebhookConfig {
  readonly signingSecret: string;
}

export interface BoundInvoice {
  readonly id: string;
  readonly orderId: string;
  readonly amountCents: number;
  readonly currency: 'EUR';
  readonly state: 'open' | 'paid' | 'void';
}

export interface WebhookEventRecord {
  readonly id: string;
  readonly type: string;
  readonly receivedAt: string;
  readonly status: 'processed' | 'ignored';
}

export interface WebhookStateStore {
  getInvoice(id: string): BoundInvoice | undefined;
  claimEvent(event: WebhookEventRecord): boolean;
  markInvoicePaid(id: string): BoundInvoice;
}

export type WebhookResult =
  | {
      readonly status: 'processed';
      readonly eventId: string;
      readonly invoiceId: string;
      readonly invoiceState: 'paid';
    }
  | {
      readonly status: 'duplicate' | 'ignored';
      readonly eventId: string;
    };

interface SignedEnvelope {
  readonly id: string;
  readonly type: string;
  readonly created: number;
  readonly data?: unknown;
}

interface InvoicePaidObject {
  readonly invoiceId: string;
  readonly orderId: string;
  readonly amountCents: number;
  readonly currency: string;
}

function boundedString(value: unknown, field: string, maximum: number): string {
  if (typeof value !== 'string' || value.length === 0 || value.length > maximum) {
    throw new BadRequestException(`Webhook ${field} is invalid`);
  }
  return value;
}

function parseEnvelope(rawBody: Buffer): SignedEnvelope {
  let value: unknown;
  try {
    value = JSON.parse(rawBody.toString('utf8')) as unknown;
  } catch {
    throw new BadRequestException('Webhook payload is not valid JSON');
  }
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new BadRequestException('Webhook payload is invalid');
  }
  const record = value as Record<string, unknown>;
  const id = boundedString(record.id, 'event id', 80);
  if (!/^[A-Za-z0-9_-]+$/.test(id)) {
    throw new BadRequestException('Webhook event id is invalid');
  }
  const type = boundedString(record.type, 'event type', 80);
  if (!Number.isSafeInteger(record.created) || Number(record.created) <= 0) {
    throw new BadRequestException('Webhook event timestamp is invalid');
  }
  return {
    id,
    type,
    created: Number(record.created),
    ...(record.data !== undefined ? { data: record.data } : {}),
  };
}

function parseInvoicePaidObject(data: unknown): InvoicePaidObject {
  if (!data || typeof data !== 'object' || Array.isArray(data)) {
    throw new BadRequestException('Webhook invoice data is invalid');
  }
  const object = (data as Record<string, unknown>).object;
  if (!object || typeof object !== 'object' || Array.isArray(object)) {
    throw new BadRequestException('Webhook invoice object is invalid');
  }
  const record = object as Record<string, unknown>;
  if (!Number.isSafeInteger(record.amountCents) || Number(record.amountCents) < 0) {
    throw new BadRequestException('Webhook invoice amount is invalid');
  }
  return {
    invoiceId: boundedString(record.invoiceId, 'invoice id', 80),
    orderId: boundedString(record.orderId, 'order id', 80),
    amountCents: Number(record.amountCents),
    currency: boundedString(record.currency, 'currency', 8).toUpperCase(),
  };
}

function parseSignatureHeader(header: string): {
  timestamp: number;
  signatures: readonly string[];
} {
  const values = header.split(',').map((part) => part.trim().split('=', 2));
  const timestampText = values.find(([key]) => key === 't')?.[1];
  const signatures = values
    .filter(([key]) => key === 'v1')
    .map(([, value]) => value ?? '');
  if (!timestampText || !/^\d+$/.test(timestampText) || signatures.length === 0) {
    throw new UnauthorizedException('Webhook signature is invalid');
  }
  const timestamp = Number(timestampText);
  if (!Number.isSafeInteger(timestamp) || timestamp <= 0) {
    throw new UnauthorizedException('Webhook signature is invalid');
  }
  return { timestamp, signatures };
}

function constantTimeSignatureMatch(
  expected: Buffer,
  candidateHex: string,
): boolean {
  const isCanonical = /^[0-9a-f]{64}$/i.test(candidateHex);
  const candidate = isCanonical
    ? Buffer.from(candidateHex, 'hex')
    : Buffer.alloc(expected.length);
  const equal = timingSafeEqual(expected, candidate);
  return isCanonical && equal;
}

@Injectable()
export class WebhookService {
  constructor(
    @Inject(WEBHOOK_CONFIG) private readonly config: WebhookConfig,
    @Inject(WEBHOOK_STATE_STORE) private readonly state: WebhookStateStore,
    private readonly securityEvents: SecurityEventsService,
  ) {
    if (Buffer.byteLength(config.signingSecret, 'utf8') < 24) {
      throw new Error('Synthetic webhook signing secret must be at least 24 bytes');
    }
  }

  handle(
    rawBody: Buffer | undefined,
    signatureHeader: string | undefined,
    correlationId: string,
    nowSeconds = Math.floor(Date.now() / 1_000),
  ): WebhookResult {
    if (!rawBody || !Buffer.isBuffer(rawBody) || rawBody.length === 0) {
      this.deny(correlationId, 'missing_raw_body');
    }
    if (rawBody.length > MAX_WEBHOOK_BYTES) {
      throw new BadRequestException('Webhook payload is too large');
    }
    if (!signatureHeader) {
      this.deny(correlationId, 'missing_signature');
    }

    let parsedSignature: ReturnType<typeof parseSignatureHeader>;
    try {
      parsedSignature = parseSignatureHeader(signatureHeader);
    } catch {
      this.deny(correlationId, 'malformed_signature');
    }
    const { timestamp, signatures } = parsedSignature;
    if (Math.abs(nowSeconds - timestamp) > WEBHOOK_TIMESTAMP_TOLERANCE_SECONDS) {
      this.deny(correlationId, 'signature_timestamp_outside_tolerance');
    }
    const expected = createHmac('sha256', this.config.signingSecret)
      .update(`${timestamp}.`, 'utf8')
      .update(rawBody)
      .digest();
    const valid = signatures
      .map((candidate) => constantTimeSignatureMatch(expected, candidate))
      .reduce((match, candidate) => match || candidate, false);
    if (!valid) {
      this.deny(correlationId, 'invalid_signature');
    }

    const envelope = parseEnvelope(rawBody);
    if (
      Math.abs(envelope.created - timestamp) >
      WEBHOOK_TIMESTAMP_TOLERANCE_SECONDS
    ) {
      throw new BadRequestException('Webhook event time is inconsistent');
    }

    if (envelope.type !== 'invoice.paid') {
      const claimed = this.state.claimEvent({
        id: envelope.id,
        type: envelope.type,
        receivedAt: new Date(nowSeconds * 1_000).toISOString(),
        status: 'ignored',
      });
      if (!claimed) {
        return { status: 'duplicate', eventId: envelope.id };
      }
      this.securityEvents.record({
        event: 'webhook_event_ignored',
        resourceType: 'webhook_event',
        resourceId: envelope.id,
        action: 'process',
        result: 'accepted',
        correlationId,
        reason: 'unknown_event_type',
      });
      return { status: 'ignored', eventId: envelope.id };
    }

    const supplied = parseInvoicePaidObject(envelope.data);
    const invoice = this.state.getInvoice(supplied.invoiceId);
    if (
      !invoice ||
      invoice.orderId !== supplied.orderId ||
      invoice.amountCents !== supplied.amountCents ||
      invoice.currency !== supplied.currency
    ) {
      throw new BadRequestException('Webhook resource binding failed');
    }
    if (invoice.state !== 'open') {
      const claimed = this.state.claimEvent({
        id: envelope.id,
        type: envelope.type,
        receivedAt: new Date(nowSeconds * 1_000).toISOString(),
        status: 'ignored',
      });
      return claimed
        ? { status: 'ignored', eventId: envelope.id }
        : { status: 'duplicate', eventId: envelope.id };
    }

    const claimed = this.state.claimEvent({
      id: envelope.id,
      type: envelope.type,
      receivedAt: new Date(nowSeconds * 1_000).toISOString(),
      status: 'processed',
    });
    if (!claimed) {
      return { status: 'duplicate', eventId: envelope.id };
    }
    // The transition uses the invoice loaded from server state. Client amount,
    // currency, order, and desired state are never written as authoritative data.
    const paid = this.state.markInvoicePaid(invoice.id);
    this.securityEvents.record({
      event: 'webhook_event_processed',
      resourceType: 'invoice',
      resourceId: invoice.id,
      action: 'mark_paid',
      result: 'accepted',
      correlationId,
      metadata: { event_id: envelope.id },
    });
    return {
      status: 'processed',
      eventId: envelope.id,
      invoiceId: paid.id,
      invoiceState: 'paid',
    };
  }

  private deny(correlationId: string, reason: string): never {
    this.securityEvents.record({
      event: 'webhook_signature_failed',
      resourceType: 'webhook_event',
      action: 'verify_signature',
      result: 'denied',
      correlationId,
      reason,
    });
    throw new UnauthorizedException('Webhook signature is invalid');
  }
}

export function defaultWebhookConfig(): WebhookConfig {
  const configured = process.env.SYNTHETIC_WEBHOOK_SECRET;
  if (
    process.env.NODE_ENV === 'production' &&
    (!configured || /^(replace|change|whsec_synthetic)/i.test(configured))
  ) {
    throw new Error(
      'SYNTHETIC_WEBHOOK_SECRET must be an explicit non-placeholder value in production',
    );
  }
  const signingSecret = configured ?? 'whsec_synthetic_local_only_do_not_reuse';
  if (Buffer.byteLength(signingSecret, 'utf8') < 24) {
    throw new Error('SYNTHETIC_WEBHOOK_SECRET must contain at least 24 bytes');
  }
  return {
    signingSecret,
  };
}
