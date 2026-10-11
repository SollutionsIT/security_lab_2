import { Injectable } from '@nestjs/common';

export interface ResetMail {
  readonly kind: 'password_reset';
  readonly recipient: string;
  readonly resetToken: string;
  readonly expiresAt: string;
}

@Injectable()
export class TestMailboxService {
  private readonly messages: ResetMail[] = [];

  sendPasswordReset(message: ResetMail): void {
    this.messages.push(structuredClone(message));
  }

  list(): ResetMail[] {
    return structuredClone(this.messages);
  }

  clear(): void {
    this.messages.length = 0;
  }
}
