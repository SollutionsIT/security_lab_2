import { Body, Controller, Delete, Get, HttpCode, HttpStatus, Param, Patch, Req } from '@nestjs/common';
import type { LabRequest } from '../common/http/lab-request';
import { UpdatePropertyDto } from './property.dto';
import { PropertiesService } from './properties.service';

@Controller('properties')
export class PropertiesController {
  constructor(private readonly properties: PropertiesService) {}

  @Get(':id')
  get(@Param('id') id: string, @Req() request: LabRequest) {
    return this.properties.get(id, request.actor!, request.correlationId);
  }

  @Patch(':id')
  update(
    @Param('id') id: string,
    @Body() dto: UpdatePropertyDto,
    @Req() request: LabRequest,
  ) {
    return this.properties.update(id, dto, request.actor!, request.correlationId);
  }

  @Delete(':id')
  @HttpCode(HttpStatus.NO_CONTENT)
  delete(@Param('id') id: string, @Req() request: LabRequest): void {
    this.properties.delete(id, request.actor!, request.correlationId);
  }
}
