const SENSITIVE_KEY =
  /authorization|cookie|password|passwd|token|secret|api[-_]?key|oauth.*code|signature|raw[-_]?body|payload|email|phone|address|name/i;
const JWT_LIKE = /\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b/g;
const BEARER_VALUE = /Bearer\s+[^\s,;]+/gi;
const CONTROL_CHARACTERS = /[\u0000-\u001F\u007F]/g;

function safeString(value: string): string {
  return value
    .replace(BEARER_VALUE, 'Bearer [REDACTED]')
    .replace(JWT_LIKE, '[REDACTED_JWT]')
    .replace(CONTROL_CHARACTERS, ' ')
    .slice(0, 512);
}

export function redactSensitive(
  value: unknown,
  depth = 0,
  seen = new WeakSet<object>(),
): unknown {
  if (value === null || typeof value === 'number' || typeof value === 'boolean') {
    return value;
  }
  if (typeof value === 'string') {
    return safeString(value);
  }
  if (depth >= 6) {
    return '[TRUNCATED]';
  }
  if (Array.isArray(value)) {
    return value.slice(0, 25).map((entry) => redactSensitive(entry, depth + 1, seen));
  }
  if (typeof value === 'object') {
    if (seen.has(value)) {
      return '[CIRCULAR]';
    }
    seen.add(value);
    const redacted: Record<string, unknown> = {};
    for (const [key, entry] of Object.entries(value).slice(0, 50)) {
      redacted[safeString(key)] = SENSITIVE_KEY.test(key)
        ? '[REDACTED]'
        : redactSensitive(entry, depth + 1, seen);
    }
    return redacted;
  }
  return '[UNSUPPORTED]';
}
