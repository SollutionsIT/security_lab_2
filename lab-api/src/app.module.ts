import { Module } from '@nestjs/common';
import { APP_GUARD } from '@nestjs/core';
import { AdminModule } from './admin/admin.module';
import { AuthModule } from './auth/auth.module';
import { BoundariesModule } from './boundaries/boundaries.module';
import { ContentTypeGuard } from './common/guards/content-type.guard';
import { JwtAuthGuard } from './common/guards/jwt-auth.guard';
import { RateLimitGuard } from './common/guards/rate-limit.guard';
import { RolesGuard } from './common/guards/roles.guard';
import { AppConfigModule } from './config/app-config';
import { ContactModule } from './contact/contact.module';
import { DataModule } from './data/in-memory.repository';
import { HealthController } from './health/health.controller';
import { InvoicesModule } from './invoices/invoices.module';
import { PropertiesModule } from './properties/properties.module';
import { SecurityModule } from './security/security-events.service';
import { TestSupportModule } from './test-support/test-support.module';

@Module({
  imports: [
    AppConfigModule,
    DataModule,
    SecurityModule,
    TestSupportModule,
    AuthModule,
    BoundariesModule,
    PropertiesModule,
    InvoicesModule,
    AdminModule,
    ContactModule,
  ],
  controllers: [HealthController],
  providers: [
    { provide: APP_GUARD, useClass: ContentTypeGuard },
    { provide: APP_GUARD, useClass: RateLimitGuard },
    { provide: APP_GUARD, useClass: JwtAuthGuard },
    { provide: APP_GUARD, useClass: RolesGuard },
  ],
})
export class AppModule {}
