import { Type } from 'class-transformer';
import {
  ArrayMaxSize,
  ArrayUnique,
  IsArray,
  IsEnum,
  IsInt,
  IsOptional,
  IsString,
  Length,
  Max,
  MaxLength,
  Min,
  ValidateIf,
  ValidateNested,
} from 'class-validator';

export enum AiSourceKind {
  Inline = 'inline',
  Url = 'url',
}

export enum AiTool {
  Summarize = 'summarize',
  ExtractEntities = 'extract_entities',
}

export class AiSourceDto {
  @IsEnum(AiSourceKind)
  kind!: AiSourceKind;

  @ValidateIf((source: AiSourceDto) => source.kind === AiSourceKind.Url)
  @IsString()
  @MaxLength(2_048)
  url?: string;
}

export class AiParseOptionsDto {
  @IsOptional()
  @IsArray()
  @ArrayMaxSize(2)
  @ArrayUnique()
  @IsEnum(AiTool, { each: true })
  tools: AiTool[] = [];

  @IsOptional()
  @IsInt()
  @Min(64)
  @Max(512)
  maxOutputCharacters = 256;
}

export class AiParseRequestDto {
  @IsString()
  @Length(1, 4_000)
  text!: string;

  @IsOptional()
  @ValidateNested()
  @Type(() => AiSourceDto)
  source?: AiSourceDto;

  @IsOptional()
  @ValidateNested()
  @Type(() => AiParseOptionsDto)
  options: AiParseOptionsDto = new AiParseOptionsDto();
}
