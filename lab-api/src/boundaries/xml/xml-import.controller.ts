import { Body, Controller, Post, Req } from '@nestjs/common';
import { AllowedContentTypes } from '../../common/decorators/security.decorators';
import type { LabRequest } from '../../common/http/lab-request';
import { XmlImportService } from './xml-import.service';

@Controller('imports')
export class XmlImportController {
  constructor(private readonly imports: XmlImportService) {}

  @Post('xml')
  @AllowedContentTypes('application/xml', 'text/xml')
  importXml(@Body() body: string | Buffer, @Req() request: LabRequest) {
    return this.imports.parse(body, request.correlationId);
  }
}
