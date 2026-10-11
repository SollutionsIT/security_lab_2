import { Type } from 'class-transformer';
import {
  IsEnum,
  IsInt,
  IsISO31661Alpha2,
  IsOptional,
  IsString,
  IsUrl,
  Max,
  MaxLength,
  Min,
  MinLength,
  ValidateNested,
} from 'class-validator';
import { PropertyState } from '../data/entities';

export class PropertyAddressDto {
  @IsString()
  @MinLength(2)
  @MaxLength(80)
  city!: string;

  @IsISO31661Alpha2()
  countryCode!: string;
}

export class UpdatePropertyDto {
  @IsOptional()
  @IsString()
  @MinLength(3)
  @MaxLength(120)
  title?: string;

  @IsOptional()
  @IsString()
  @MaxLength(2_000)
  description?: string;

  @IsOptional()
  @Type(() => Number)
  @IsInt()
  @Min(0)
  @Max(1_000_000_000)
  askingPriceCents?: number;

  @IsOptional()
  @IsUrl({ protocols: ['https'], require_protocol: true, require_valid_protocol: true })
  @MaxLength(512)
  listingUrl?: string;

  @IsOptional()
  @ValidateNested()
  @Type(() => PropertyAddressDto)
  address?: PropertyAddressDto;

  @IsOptional()
  @IsEnum(PropertyState)
  state?: PropertyState;
}
