import {
  Controller,
  Get,
  Header,
  Param,
  Post,
  Req,
  StreamableFile,
  UploadedFile,
  UseInterceptors,
} from '@nestjs/common';
import { FileInterceptor } from '@nestjs/platform-express';
import type { LabRequest } from '../../common/http/lab-request';
import { AllowedContentTypes } from '../../common/decorators/security.decorators';
import {
  MAX_UPLOAD_BYTES,
  type MultipartFile,
  UploadService,
} from './upload.service';

@Controller('uploads')
export class UploadController {
  constructor(private readonly uploads: UploadService) {}

  @Post()
  @AllowedContentTypes('multipart/form-data')
  @UseInterceptors(
    FileInterceptor('file', {
      // Keep the submitted path only in memory so the service can reject path
      // separators instead of allowing Busboy to silently basename them.
      preservePath: true,
      limits: { fileSize: MAX_UPLOAD_BYTES, files: 1, fields: 0 },
    }),
  )
  async upload(
    @UploadedFile() file: MultipartFile | undefined,
    @Req() request: LabRequest,
  ) {
    return this.uploads.store(file, request.actor!, request.correlationId);
  }

  @Get(':storedName')
  @Header('X-Content-Type-Options', 'nosniff')
  @Header('Content-Security-Policy', "default-src 'none'; sandbox")
  @Header('Cache-Control', 'private, no-store')
  async download(
    @Param('storedName') storedName: string,
    @Req() request: LabRequest,
  ): Promise<StreamableFile> {
    const download = await this.uploads.download(
      storedName,
      request.actor!,
      request.correlationId,
    );
    return new StreamableFile(download.body, {
      type: download.headers['Content-Type'],
      disposition: download.headers['Content-Disposition'],
      length: download.body.length,
    });
  }
}
