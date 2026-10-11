import { Body, Controller, HttpCode, HttpStatus, Post, Req } from '@nestjs/common';
import { Public, RateLimit } from '../common/decorators/security.decorators';
import type { LabRequest } from '../common/http/lab-request';
import { SecurityEventsService } from '../security/security-events.service';
import { ContactDto } from './contact.dto';

@Controller('public')
export class ContactController {
  constructor(private readonly securityEvents: SecurityEventsService) {}

  @Public()
  @Post('contact')
  @HttpCode(HttpStatus.ACCEPTED)
  @RateLimit('public_form')
  submit(@Body() _dto: ContactDto, @Req() request: LabRequest) {
    this.securityEvents.record({
      event: 'public_contact_accepted',
      actorId: 'anonymous',
      resourceType: 'contact',
      action: 'create',
      result: 'accepted',
      correlationId: request.correlationId,
    });
    return { message: 'Contact request accepted' };
  }
}
