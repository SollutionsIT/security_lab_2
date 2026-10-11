import { Type } from 'class-transformer';
import {
  IsEmail,
  IsInt,
  IsOptional,
  IsString,
  IsUrl,
  Max,
  MaxLength,
  Min,
  MinLength,
  ValidateNested,
} from 'class-validator';

export class ContactContextDto {
  @IsOptional()
  @IsUrl({ protocols: ['https'], require_protocol: true, require_valid_protocol: true })
  @MaxLength(512)
  sourceUrl?: string;

  @Type(() => Number)
  @IsInt()
  @Min(1)
  @Max(5)
  urgency!: number;
}

export class ContactDto {
  @IsEmail()
  @MaxLength(254)
  email!: string;

  @IsString()
  @MinLength(3)
  @MaxLength(120)
  subject!: string;

  @IsString()
  @MinLength(10)
  @MaxLength(2_000)
  message!: string;

  @IsOptional()
  @ValidateNested()
  @Type(() => ContactContextDto)
  context?: ContactContextDto;
}
