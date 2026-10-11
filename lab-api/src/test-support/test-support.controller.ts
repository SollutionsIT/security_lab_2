import { Controller, Get, HttpCode, HttpStatus, Post, UseGuards } from '@nestjs/common';
import { AllowedContentTypes, Public } from '../common/decorators/security.decorators';
import { UploadService } from '../boundaries/upload/upload.service';
import { TestOnlyGuard } from '../common/guards/test-only.guard';
import { InMemoryRepository } from '../data/in-memory.repository';
import { RateLimiterService } from '../security/rate-limiter.service';
import { SecurityEventsService } from '../security/security-events.service';
import { TestMailboxService } from './test-mailbox.service';

@Public()
@UseGuards(TestOnlyGuard)
@Controller('__test')
export class TestSupportController {
  constructor(
    private readonly repository: InMemoryRepository,
    private readonly mailbox: TestMailboxService,
    private readonly securityEvents: SecurityEventsService,
    private readonly rateLimiter: RateLimiterService,
    private readonly uploads: UploadService,
  ) {}

  @Post('reset')
  @HttpCode(HttpStatus.NO_CONTENT)
  @AllowedContentTypes()
  async reset(): Promise<void> {
    this.repository.reset();
    this.mailbox.clear();
    this.securityEvents.clear();
    this.rateLimiter.clear();
    await this.uploads.clearStorage();
  }

  @Get('state')
  state() {
    return this.repository.sanitizedState();
  }

  @Get('mailbox')
  mailboxMessages() {
    return { messages: this.mailbox.list() };
  }

  @Get('logs')
  logs() {
    return { events: this.securityEvents.list() };
  }
}
