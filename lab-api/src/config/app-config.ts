import { Global, Module } from '@nestjs/common';

export type RuntimeEnvironment = 'development' | 'test' | 'production';

export interface AppConfig {
  readonly environment: RuntimeEnvironment;
  readonly host: string;
  readonly port: number;
  readonly jsonBodyLimitBytes: number;
  readonly jwt: {
    readonly secret: string;
    readonly issuer: string;
    readonly audience: string;
    readonly ttlSeconds: number;
  };
  readonly resetTokenTtlSeconds: number;
  readonly labTestMode: boolean;
  readonly labTestKey?: string;
}

export const APP_CONFIG = Symbol('APP_CONFIG');

const DEVELOPMENT_JWT_PLACEHOLDER = 'replace-me';
const PLACEHOLDER_PATTERNS = [
  /^replace[-_ ]?me/i,
  /^change[-_ ]?me/i,
  /^development[-_ ]?only/i,
  /^example/i,
];

function parseEnvironment(value: string | undefined): RuntimeEnvironment {
  const environment = value ?? 'development';
  if (!['development', 'test', 'production'].includes(environment)) {
    throw new Error('NODE_ENV must be development, test, or production');
  }
  return environment as RuntimeEnvironment;
}

function parseInteger(
  value: string | undefined,
  fallback: number,
  name: string,
  minimum: number,
  maximum: number,
): number {
  const candidate = value === undefined ? fallback : Number(value);
  if (!Number.isInteger(candidate) || candidate < minimum || candidate > maximum) {
    throw new Error(`${name} must be an integer between ${minimum} and ${maximum}`);
  }
  return candidate;
}

function parseBoolean(value: string | undefined, name: string): boolean {
  if (value === undefined) {
    return false;
  }
  if (value === 'true') {
    return true;
  }
  if (value === 'false') {
    return false;
  }
  throw new Error(`${name} must be either true or false`);
}

function requireBoundedText(
  value: string | undefined,
  fallback: string,
  name: string,
): string {
  const candidate = (value ?? fallback).trim();
  if (candidate.length < 3 || candidate.length > 128) {
    throw new Error(`${name} must contain between 3 and 128 characters`);
  }
  return candidate;
}

function isPlaceholder(value: string): boolean {
  return PLACEHOLDER_PATTERNS.some((pattern) => pattern.test(value));
}

export function loadAppConfig(environment: NodeJS.ProcessEnv): AppConfig {
  const runtimeEnvironment = parseEnvironment(environment.NODE_ENV);
  const jwtSecret = environment.JWT_SECRET ?? DEVELOPMENT_JWT_PLACEHOLDER;
  const labTestMode = parseBoolean(environment.LAB_TEST_MODE, 'LAB_TEST_MODE');
  const labTestKey = environment.LAB_TEST_KEY?.trim();

  if (runtimeEnvironment === 'production') {
    if (Buffer.byteLength(jwtSecret, 'utf8') < 32 || isPlaceholder(jwtSecret)) {
      throw new Error(
        'JWT_SECRET must be non-placeholder and at least 32 bytes in production',
      );
    }
    if (labTestMode) {
      throw new Error('LAB_TEST_MODE cannot be enabled in production');
    }
  }

  if (labTestMode && (!labTestKey || labTestKey.length < 16 || isPlaceholder(labTestKey))) {
    throw new Error(
      'LAB_TEST_KEY must be a non-placeholder value of at least 16 characters when LAB_TEST_MODE is enabled',
    );
  }

  return Object.freeze({
    environment: runtimeEnvironment,
    host: (environment.HOST ?? '127.0.0.1').trim() || '127.0.0.1',
    port: parseInteger(environment.PORT, 3001, 'PORT', 1, 65_535),
    jsonBodyLimitBytes: parseInteger(
      environment.JSON_BODY_LIMIT_BYTES,
      32_768,
      'JSON_BODY_LIMIT_BYTES',
      1_024,
      1_048_576,
    ),
    jwt: Object.freeze({
      secret: jwtSecret,
      issuer: requireBoundedText(
        environment.JWT_ISSUER,
        'company-security-lab',
        'JWT_ISSUER',
      ),
      audience: requireBoundedText(
        environment.JWT_AUDIENCE,
        'company-security-lab-clients',
        'JWT_AUDIENCE',
      ),
      ttlSeconds: parseInteger(
        environment.JWT_TTL_SECONDS,
        900,
        'JWT_TTL_SECONDS',
        60,
        3_600,
      ),
    }),
    resetTokenTtlSeconds: parseInteger(
      environment.RESET_TOKEN_TTL_SECONDS,
      900,
      'RESET_TOKEN_TTL_SECONDS',
      60,
      3_600,
    ),
    labTestMode,
    ...(labTestKey ? { labTestKey } : {}),
  });
}

@Global()
@Module({
  providers: [
    {
      provide: APP_CONFIG,
      useFactory: (): AppConfig => loadAppConfig(process.env),
    },
  ],
  exports: [APP_CONFIG],
})
export class AppConfigModule {}
