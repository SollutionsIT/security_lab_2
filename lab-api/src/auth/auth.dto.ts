import {
  IsEmail,
  IsString,
  IsStrongPassword,
  Matches,
  MaxLength,
  MinLength,
} from 'class-validator';

export class LoginDto {
  @IsEmail()
  @MaxLength(254)
  email!: string;

  @IsString()
  @MinLength(12)
  @MaxLength(128)
  password!: string;
}

export class ResetPasswordRequestDto {
  @IsEmail()
  @MaxLength(254)
  email!: string;
}

export class ResetPasswordConfirmDto {
  @IsString()
  @MinLength(43)
  @MaxLength(128)
  @Matches(/^[A-Za-z0-9_-]+$/)
  token!: string;

  @IsString()
  @MaxLength(128)
  @IsStrongPassword({
    minLength: 12,
    minLowercase: 1,
    minUppercase: 1,
    minNumbers: 1,
    minSymbols: 1,
  })
  newPassword!: string;
}
