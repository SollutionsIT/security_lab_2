import { Global, Injectable, Module } from '@nestjs/common';
import { createDeterministicSeedHash } from '../auth/password.service';
import {
  Attachment,
  Invoice,
  InvoiceState,
  Property,
  PropertyState,
  ResetTokenRecord,
  Role,
  User,
  WebhookEvent,
} from './entities';

const SEED_TIME = '2026-01-15T10:00:00.000Z';

function clone<T>(value: T): T {
  return structuredClone(value);
}

export interface PropertyChanges {
  readonly title?: string;
  readonly description?: string;
  readonly askingPriceCents?: number;
  readonly listingUrl?: string;
  readonly address?: { readonly city: string; readonly countryCode: string };
  readonly state?: PropertyState;
}

@Injectable()
export class InMemoryRepository {
  private users = new Map<string, User>();
  private properties = new Map<string, Property>();
  private invoices = new Map<string, Invoice>();
  private attachments = new Map<string, Attachment>();
  private webhookEvents = new Map<string, WebhookEvent>();
  private resetTokens = new Map<string, ResetTokenRecord>();

  constructor() {
    this.reset();
  }

  reset(): void {
    const users: User[] = [
      {
        id: 'user-alice',
        email: 'alice@example.test',
        passwordHash: createDeterministicSeedHash(
          'Alice-Local-Only!42',
          'alice-seed-salt-01',
        ),
        role: Role.User,
        isVerified: true,
      },
      {
        id: 'user-bob',
        email: 'bob@example.test',
        passwordHash: createDeterministicSeedHash(
          'Bob-Local-Only!42',
          'bob-seed-salt---02',
        ),
        role: Role.User,
        isVerified: true,
      },
      {
        id: 'admin-ada',
        email: 'admin@example.test',
        passwordHash: createDeterministicSeedHash(
          'Admin-Local-Only!42',
          'admin-seed-salt-03',
        ),
        role: Role.Admin,
        isVerified: true,
      },
    ];

    const properties: Property[] = [
      {
        id: 'property-alice',
        ownerId: 'user-alice',
        title: 'Synthetic Alice Apartment',
        description: 'A deterministic record used only by the local security lab.',
        askingPriceCents: 250_000_00,
        listingUrl: 'https://example.test/properties/property-alice',
        address: { city: 'Example City', countryCode: 'AT' },
        state: PropertyState.Draft,
        updatedAt: SEED_TIME,
      },
      {
        id: 'property-bob',
        ownerId: 'user-bob',
        title: 'Synthetic Bob Studio',
        description: 'A second deterministic ownership boundary.',
        askingPriceCents: 175_000_00,
        address: { city: 'Sample Town', countryCode: 'DE' },
        state: PropertyState.Published,
        updatedAt: SEED_TIME,
      },
    ];

    const invoices: Invoice[] = [
      {
        id: 'invoice-alice',
        orderId: 'order-alice',
        ownerId: 'user-alice',
        amountCents: 12_500,
        currency: 'EUR',
        state: InvoiceState.Open,
        issuedAt: SEED_TIME,
      },
      {
        id: 'invoice-bob',
        orderId: 'order-bob',
        ownerId: 'user-bob',
        amountCents: 8_500,
        currency: 'EUR',
        state: InvoiceState.Paid,
        issuedAt: SEED_TIME,
      },
    ];

    const attachments: Attachment[] = [
      {
        id: 'attachment-alice-1',
        ownerId: 'user-alice',
        propertyId: 'property-alice',
        filename: 'synthetic-floorplan.pdf',
        mediaType: 'application/pdf',
        sizeBytes: 1_024,
        storageKey: 'lab/attachments/attachment-alice-1',
        createdAt: SEED_TIME,
      },
    ];

    this.users = new Map(users.map((user) => [user.id, user]));
    this.properties = new Map(properties.map((property) => [property.id, property]));
    this.invoices = new Map(invoices.map((invoice) => [invoice.id, invoice]));
    this.attachments = new Map(
      attachments.map((attachment) => [attachment.id, attachment]),
    );
    this.webhookEvents = new Map();
    this.resetTokens = new Map();
  }

  findUserByEmail(email: string): User | undefined {
    const normalized = email.trim().toLowerCase();
    const user = [...this.users.values()].find((candidate) => candidate.email === normalized);
    return user ? clone(user) : undefined;
  }

  findUserById(id: string): User | undefined {
    const user = this.users.get(id);
    return user ? clone(user) : undefined;
  }

  updateUserPassword(userId: string, passwordHash: string): void {
    const user = this.users.get(userId);
    if (!user) {
      throw new Error('User disappeared during password reset');
    }
    user.passwordHash = passwordHash;
  }

  saveResetToken(record: ResetTokenRecord): void {
    this.resetTokens.set(record.tokenDigest, clone(record));
  }

  consumeValidResetToken(tokenDigest: string, now: number): ResetTokenRecord | undefined {
    const record = this.resetTokens.get(tokenDigest);
    if (!record) {
      return undefined;
    }
    this.resetTokens.delete(tokenDigest);
    if (record.expiresAt <= now) {
      return undefined;
    }
    return clone(record);
  }

  deleteResetTokensForUser(userId: string): void {
    for (const [digest, record] of this.resetTokens.entries()) {
      if (record.userId === userId) {
        this.resetTokens.delete(digest);
      }
    }
  }

  getProperty(id: string): Property | undefined {
    const property = this.properties.get(id);
    return property ? clone(property) : undefined;
  }

  updateProperty(id: string, changes: PropertyChanges, updatedAt: string): Property {
    const property = this.properties.get(id);
    if (!property) {
      throw new Error('Property disappeared during update');
    }

    if (changes.title !== undefined) property.title = changes.title;
    if (changes.description !== undefined) property.description = changes.description;
    if (changes.askingPriceCents !== undefined) {
      property.askingPriceCents = changes.askingPriceCents;
    }
    if (changes.listingUrl !== undefined) property.listingUrl = changes.listingUrl;
    if (changes.address !== undefined) property.address = clone(changes.address);
    if (changes.state !== undefined) property.state = changes.state;
    property.updatedAt = updatedAt;
    return clone(property);
  }

  deleteProperty(id: string): void {
    this.properties.delete(id);
  }

  getInvoice(id: string): Invoice | undefined {
    const invoice = this.invoices.get(id);
    return invoice ? clone(invoice) : undefined;
  }

  updateInvoiceState(id: string, state: InvoiceState): Invoice | undefined {
    const invoice = this.invoices.get(id);
    if (!invoice) return undefined;
    invoice.state = state;
    return clone(invoice);
  }

  saveAttachment(attachment: Attachment): void {
    this.attachments.set(attachment.id, clone(attachment));
  }

  findAttachmentByStorageKey(storageKey: string): Attachment | undefined {
    const attachment = [...this.attachments.values()].find(
      (candidate) => candidate.storageKey === storageKey,
    );
    return attachment ? clone(attachment) : undefined;
  }

  getWebhookEvent(id: string): WebhookEvent | undefined {
    const event = this.webhookEvents.get(id);
    return event ? clone(event) : undefined;
  }

  claimWebhookEvent(event: WebhookEvent): boolean {
    if (this.webhookEvents.has(event.id)) return false;
    this.webhookEvents.set(event.id, clone(event));
    return true;
  }

  saveWebhookEvent(event: WebhookEvent): void {
    this.webhookEvents.set(event.id, clone(event));
  }

  sanitizedState(): Record<string, unknown> {
    return {
      seedAliases: {
        userA: {
          userId: 'user-alice',
          propertyId: 'property-alice',
          invoiceId: 'invoice-alice',
        },
        userB: {
          userId: 'user-bob',
          propertyId: 'property-bob',
          invoiceId: 'invoice-bob',
        },
        admin: { userId: 'admin-ada' },
      },
      users: [...this.users.values()].map(({ id, role, isVerified }) => ({
        id,
        role,
        isVerified,
      })),
      properties: [...this.properties.values()].map(clone),
      invoices: [...this.invoices.values()].map(clone),
      attachments: [...this.attachments.values()].map(clone),
      webhookEvents: [...this.webhookEvents.values()].map(clone),
      resetTokenCount: this.resetTokens.size,
    };
  }
}

@Global()
@Module({
  providers: [InMemoryRepository],
  exports: [InMemoryRepository],
})
export class DataModule {}
