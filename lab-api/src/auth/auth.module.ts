import { Module } from '@nestjs/common';
import { AuthController } from './auth.controller';
import { AuthService } from './auth.service';
import { JwtTokenService } from './jwt-token.service';
import { PasswordService } from './password.service';
import { TestSupportModule } from '../test-support/test-support.module';

@Module({
  imports: [TestSupportModule],
  controllers: [AuthController],
  providers: [AuthService, JwtTokenService, PasswordService],
  exports: [JwtTokenService],
})
export class AuthModule {}
