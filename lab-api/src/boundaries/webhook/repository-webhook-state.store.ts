import { Injectable } from '@nestjs/common';
import { InMemoryRepository } from '../../data/in-memory.repository';
import { InvoiceState } from '../../data/entities';
import type {
  BoundInvoice,
  WebhookEventRecord,
  WebhookStateStore,
} from './webhook.service';

function boundaryState(state: InvoiceState): BoundInvoice['state'] {
  if (state === InvoiceState.Open) return 'open';
  if (state === InvoiceState.Paid) return 'paid';
  return 'void';
}

@Injectable()
export class RepositoryWebhookStateStore implements WebhookStateStore {
  constructor(private readonly repository: InMemoryRepository) {}

  getInvoice(id: string): BoundInvoice | undefined {
    const invoice = this.repository.getInvoice(id);
    if (!invoice) {
      return undefined;
    }
    return {
      id: invoice.id,
      orderId: invoice.orderId,
      amountCents: invoice.amountCents,
      currency: invoice.currency,
      state: boundaryState(invoice.state),
    };
  }

  claimEvent(event: WebhookEventRecord): boolean {
    return this.repository.claimWebhookEvent({
      id: event.id,
      type: event.type,
      receivedAt: event.receivedAt,
      status: event.status,
      ...(event.status === 'processed' ? { processedAt: event.receivedAt } : {}),
    });
  }

  markInvoicePaid(id: string): BoundInvoice {
    const invoice = this.repository.updateInvoiceState(id, InvoiceState.Paid);
    if (!invoice) {
      throw new Error('Invoice disappeared during webhook processing');
    }
    return {
      id: invoice.id,
      orderId: invoice.orderId,
      amountCents: invoice.amountCents,
      currency: invoice.currency,
      state: boundaryState(invoice.state),
    };
  }
}
