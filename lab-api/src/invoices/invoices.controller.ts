import { Controller, Get, Param, Req } from '@nestjs/common';
import type { LabRequest } from '../common/http/lab-request';
import { InvoicesService } from './invoices.service';

@Controller('invoices')
export class InvoicesController {
  constructor(private readonly invoices: InvoicesService) {}

  @Get(':id')
  get(@Param('id') id: string, @Req() request: LabRequest) {
    return this.invoices.get(id, request.actor!, request.correlationId);
  }
}
