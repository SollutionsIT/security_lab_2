import { Injectable, NotFoundException } from '@nestjs/common';
import {
  AuthenticatedActor,
  Property,
  PropertyState,
  Role,
} from '../data/entities';
import { InMemoryRepository } from '../data/in-memory.repository';
import { SecurityEventsService } from '../security/security-events.service';
import { UpdatePropertyDto } from './property.dto';

@Injectable()
export class PropertiesService {
  constructor(
    private readonly repository: InMemoryRepository,
    private readonly securityEvents: SecurityEventsService,
  ) {}

  get(id: string, actor: AuthenticatedActor, correlationId: string): Property {
    const property = this.repository.getProperty(id);
    if (!property || !this.isAllowed(actor, property, 'read')) {
      if (property) this.denied(actor, id, 'read', correlationId);
      throw new NotFoundException('Property not found');
    }
    return property;
  }

  update(
    id: string,
    dto: UpdatePropertyDto,
    actor: AuthenticatedActor,
    correlationId: string,
  ): Property {
    const property = this.repository.getProperty(id);
    if (!property || !this.isAllowed(actor, property, 'update')) {
      if (property) this.denied(actor, id, 'update', correlationId);
      throw new NotFoundException('Property not found');
    }
    if (Object.keys(dto).length === 0) {
      return property;
    }
    return this.repository.updateProperty(id, dto, new Date().toISOString());
  }

  delete(id: string, actor: AuthenticatedActor, correlationId: string): void {
    const property = this.repository.getProperty(id);
    if (!property || !this.isAllowed(actor, property, 'delete')) {
      if (property) this.denied(actor, id, 'delete', correlationId);
      throw new NotFoundException('Property not found');
    }
    this.repository.deleteProperty(id);
  }

  private isAllowed(
    actor: AuthenticatedActor,
    property: Property,
    action: 'read' | 'update' | 'delete',
  ): boolean {
    if (actor.role === Role.Admin) return true;
    if (actor.id !== property.ownerId) return false;
    return action === 'read' || property.state !== PropertyState.Archived;
  }

  private denied(
    actor: AuthenticatedActor,
    resourceId: string,
    action: string,
    correlationId: string,
  ): void {
    this.securityEvents.record({
      event: 'authorization_denied',
      actorId: actor.id,
      resourceType: 'property',
      resourceId,
      action,
      result: 'denied',
      correlationId,
      reason: 'owner_role_or_state_policy',
    });
  }
}
