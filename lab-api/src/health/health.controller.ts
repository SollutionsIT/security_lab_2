import { Controller, Get } from '@nestjs/common';
import { Public } from '../common/decorators/security.decorators';

@Controller('health')
export class HealthController {
  @Public()
  @Get()
  health() {
    return { status: 'ok', service: 'company-security-lab-api' };
  }
}
