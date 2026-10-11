export enum Role {
  User = 'user',
  Admin = 'admin',
}

export enum PropertyState {
  Draft = 'draft',
  Published = 'published',
  Archived = 'archived',
}

export enum InvoiceState {
  Open = 'open',
  Paid = 'paid',
  Void = 'void',
}

export interface User {
  readonly id: string;
  readonly email: string;
  passwordHash: string;
  readonly role: Role;
  readonly isVerified: boolean;
}

export interface PropertyAddress {
  readonly city: string;
  readonly countryCode: string;
}

export interface Property {
  readonly id: string;
  readonly ownerId: string;
  title: string;
  description: string;
  askingPriceCents: number;
  listingUrl?: string;
  address: PropertyAddress;
  state: PropertyState;
  updatedAt: string;
}

export interface Invoice {
  readonly id: string;
  readonly orderId: string;
  readonly ownerId: string;
  readonly amountCents: number;
  readonly currency: 'EUR';
  state: InvoiceState;
  readonly issuedAt: string;
}

export interface Attachment {
  readonly id: string;
  readonly ownerId: string;
  readonly propertyId: string;
  readonly filename: string;
  readonly mediaType: string;
  readonly sizeBytes: number;
  readonly storageKey: string;
  readonly createdAt: string;
}

export interface WebhookEvent {
  readonly id: string;
  readonly type: string;
  readonly receivedAt: string;
  processedAt?: string;
  status: 'received' | 'processed' | 'ignored';
}

export interface ResetTokenRecord {
  readonly tokenDigest: string;
  readonly userId: string;
  readonly expiresAt: number;
  readonly createdAt: number;
}

export interface AuthenticatedActor {
  readonly id: string;
  readonly role: Role;
}
