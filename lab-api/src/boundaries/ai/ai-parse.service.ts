import { BadGatewayException, BadRequestException, Inject, Injectable } from '@nestjs/common';
import { SecurityEventsService } from '../../security/security-events.service';
import { SsrfUrlPolicy } from '../ssrf/ssrf-url-policy';
import {
  AiParseRequestDto,
  AiSourceKind,
  AiTool,
} from './ai-parse.dto';

export const AI_MODEL_GATEWAY = Symbol('AI_MODEL_GATEWAY');
export const AI_LIMITS = Object.freeze({
  maxInputBytes: 8_192,
  maxOutputCharacters: 512,
  maxTools: 2,
  maxLabels: 5,
});

export interface AiModelInput {
  readonly untrustedText: string;
  readonly allowedTools: readonly AiTool[];
}

export interface AiModelGateway {
  generate(input: AiModelInput): unknown;
}

export interface ValidatedAiResult {
  readonly summary: string;
  readonly labels: readonly string[];
  readonly toolSuggestions: readonly AiTool[];
  readonly sourceUrlValidated: boolean;
}

const OUTPUT_LABELS = new Set(['document', 'short_text', 'long_text']);
const TOOL_ALLOWLIST = new Set<string>(Object.values(AiTool));

function stringArray(
  value: unknown,
  maximumItems: number,
  maximumItemLength: number,
): string[] | undefined {
  if (
    !Array.isArray(value) ||
    value.length > maximumItems ||
    value.some(
      (entry) =>
        typeof entry !== 'string' ||
        entry.length === 0 ||
        entry.length > maximumItemLength,
    )
  ) {
    return undefined;
  }
  return value as string[];
}

@Injectable()
export class MockAiModelGateway implements AiModelGateway {
  generate(input: AiModelInput): unknown {
    // This is deterministic local code: it performs no DNS, HTTP, file, or tool
    // calls and intentionally never echoes the untrusted input.
    return {
      summary: 'Synthetic model output validated at the application boundary.',
      labels: [
        'document',
        input.untrustedText.length > 500 ? 'long_text' : 'short_text',
      ],
      toolSuggestions: [...input.allowedTools],
    };
  }
}

@Injectable()
export class AiParseService {
  constructor(
    @Inject(AI_MODEL_GATEWAY) private readonly model: AiModelGateway,
    private readonly sourcePolicy: SsrfUrlPolicy,
    private readonly securityEvents: SecurityEventsService,
  ) {}

  parse(
    request: AiParseRequestDto,
    actorId: string,
    correlationId: string,
  ): ValidatedAiResult {
    if (Buffer.byteLength(request.text, 'utf8') > AI_LIMITS.maxInputBytes) {
      throw new BadRequestException('AI input byte quota exceeded');
    }
    const tools = request.options?.tools ?? [];
    if (
      tools.length > AI_LIMITS.maxTools ||
      tools.some((tool) => !TOOL_ALLOWLIST.has(tool))
    ) {
      throw new BadRequestException('AI tool is not allowlisted');
    }

    let sourceUrlValidated = false;
    if (request.source?.kind === AiSourceKind.Url) {
      if (!request.source.url) {
        throw new BadRequestException('URL source requires a URL');
      }
      // Policy validation only. This lab deliberately has no fetch implementation.
      this.sourcePolicy.validate(request.source.url);
      sourceUrlValidated = true;
    }

    // Prompt text remains untrusted data. There is no secret-bearing system
    // prompt and model output cannot directly invoke a tool.
    const rawOutput = this.model.generate({
      untrustedText: request.text,
      allowedTools: tools,
    });
    const validated = this.validateOutput(
      rawOutput,
      tools,
      Math.min(
        request.options?.maxOutputCharacters ?? 256,
        AI_LIMITS.maxOutputCharacters,
      ),
    );

    this.securityEvents.record({
      event: 'ai_parse_completed',
      actorId,
      resourceType: 'ai_parse',
      action: 'parse',
      result: 'accepted',
      correlationId,
      metadata: {
        input_bytes: Buffer.byteLength(request.text, 'utf8'),
        output_characters: validated.summary.length,
        tool_count: validated.toolSuggestions.length,
        source_url_validated: sourceUrlValidated,
      },
    });
    return { ...validated, sourceUrlValidated };
  }

  private validateOutput(
    output: unknown,
    requestedTools: readonly AiTool[],
    maximumOutputCharacters: number,
  ): Omit<ValidatedAiResult, 'sourceUrlValidated'> {
    if (!output || typeof output !== 'object' || Array.isArray(output)) {
      throw new BadGatewayException('Model output failed validation');
    }
    const record = output as Record<string, unknown>;
    if (
      Object.keys(record).some(
        (key) => !['summary', 'labels', 'toolSuggestions'].includes(key),
      ) ||
      typeof record.summary !== 'string' ||
      record.summary.length === 0 ||
      record.summary.length > maximumOutputCharacters
    ) {
      throw new BadGatewayException('Model output failed validation');
    }
    const labels = stringArray(record.labels, AI_LIMITS.maxLabels, 32);
    const toolSuggestions = stringArray(
      record.toolSuggestions,
      AI_LIMITS.maxTools,
      32,
    );
    if (
      !labels ||
      labels.some((label) => !OUTPUT_LABELS.has(label)) ||
      !toolSuggestions ||
      toolSuggestions.some(
        (tool) =>
          !TOOL_ALLOWLIST.has(tool) || !requestedTools.includes(tool as AiTool),
      )
    ) {
      throw new BadGatewayException('Model output failed validation');
    }
    return {
      summary: record.summary,
      labels,
      toolSuggestions: toolSuggestions as AiTool[],
    };
  }
}
