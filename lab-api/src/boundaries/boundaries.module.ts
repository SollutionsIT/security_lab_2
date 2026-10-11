import { Module } from '@nestjs/common';
import { AiParseModule } from './ai/ai-parse.module';
import { UploadModule } from './upload/upload.module';
import { WebhookModule } from './webhook/webhook.module';
import { XmlImportModule } from './xml/xml-import.module';

@Module({
  imports: [WebhookModule, UploadModule, XmlImportModule, AiParseModule],
  exports: [WebhookModule, UploadModule, XmlImportModule, AiParseModule],
})
export class BoundariesModule {}
