import { Module } from '@nestjs/common';
import { UploadModule } from '../boundaries/upload/upload.module';
import { TestOnlyGuard } from '../common/guards/test-only.guard';
import { TestMailboxService } from './test-mailbox.service';
import { TestSupportController } from './test-support.controller';

@Module({
  imports: [UploadModule],
  controllers: [TestSupportController],
  providers: [TestMailboxService, TestOnlyGuard],
  exports: [TestMailboxService],
})
export class TestSupportModule {}
