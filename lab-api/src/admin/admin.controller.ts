import { Controller, Get } from '@nestjs/common';
import { Roles } from '../common/decorators/security.decorators';
import { Role } from '../data/entities';
import { SecurityEventsService } from '../security/security-events.service';

@Controller('admin')
export class AdminController {
  constructor(private readonly securityEvents: SecurityEventsService) {}

  @Get('audit-events')
  @Roles(Role.Admin)
  auditEvents() {
    return { events: this.securityEvents.list() };
  }
}
