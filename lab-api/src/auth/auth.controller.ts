import { Body, Controller, HttpCode, HttpStatus, Post, Req } from '@nestjs/common';
import { Public, RateLimit } from '../common/decorators/security.decorators';
import type { LabRequest } from '../common/http/lab-request';
import {
  LoginDto,
  ResetPasswordConfirmDto,
  ResetPasswordRequestDto,
} from './auth.dto';
import { AuthService } from './auth.service';

@Public()
@Controller('auth')
export class AuthController {
  constructor(private readonly auth: AuthService) {}

  @Post('login')
  @HttpCode(HttpStatus.OK)
  @RateLimit('login')
  login(@Body() dto: LoginDto, @Req() request: LabRequest) {
    return this.auth.login(dto, request.correlationId);
  }

  @Post('reset-password')
  @HttpCode(HttpStatus.ACCEPTED)
  @RateLimit('reset')
  requestReset(@Body() dto: ResetPasswordRequestDto, @Req() request: LabRequest) {
    return this.auth.requestReset(dto, request.correlationId);
  }

  @Post('reset-password/confirm')
  @HttpCode(HttpStatus.OK)
  @RateLimit('reset')
  confirmReset(@Body() dto: ResetPasswordConfirmDto, @Req() request: LabRequest) {
    return this.auth.confirmReset(dto, request.correlationId);
  }
}
