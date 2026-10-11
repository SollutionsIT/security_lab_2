import { Injectable, NotFoundException } from '@nestjs/common';
import { AuthenticatedActor, Invoice, Role } from '../data/entities';
import { InMemoryRepository } from '../data/in-memory.repository';
import { SecurityEventsService } from '../security/security-events.service';

@Injectable()
export class InvoicesService {
  constructor(
    private readonly repository: InMemoryRepository,
    private readonly securityEvents: SecurityEventsService,
  ) {}

  get(id: string, actor: AuthenticatedActor, correlationId: string): Invoice {
    const invoice = this.repository.getInvoice(id);
    if (!invoice || (actor.role !== Role.Admin && actor.id !== invoice.ownerId)) {
      if (invoice) {
        this.securityEvents.record({
          event: 'authorization_denied',
          actorId: actor.id,
          resourceType: 'invoice',
          resourceId: id,
          action: 'read',
          result: 'denied',
          correlationId,
          reason: 'not_owner_or_admin',
        });
      }
      throw new NotFoundException('Invoice not found');
    }
    return invoice;
  }
}
