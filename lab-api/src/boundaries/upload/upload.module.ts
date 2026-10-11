import { Module } from '@nestjs/common';
import { UploadController } from './upload.controller';
import { defaultUploadConfig, UPLOAD_CONFIG, UploadService } from './upload.service';

@Module({
  controllers: [UploadController],
  providers: [
    { provide: UPLOAD_CONFIG, useFactory: defaultUploadConfig },
    UploadService,
  ],
  exports: [UploadService],
})
export class UploadModule {}
