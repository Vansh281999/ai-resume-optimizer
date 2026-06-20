export type ClassName = string | number | boolean | null | undefined;

export function cn(...inputs: ClassName[]): string {
  return inputs.filter(Boolean).join(' ');
}

export function formatScore(value: string | number | undefined): string {
  if (typeof value !== 'number') {
    const numericValue = Number(value);
    if (!Number.isFinite(numericValue)) {
      return '0';
    }
    return `${Math.round(numericValue)}%`;
  }
  if (Number.isNaN(value)) {
    return '0';
  }
  return `${Math.round(value)}%`;
}

export function parseCommaSeparated(value: string): string[] {
  return value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);
}

export function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return redactSensitiveData(error.message);
  }
  return 'Something went wrong. Please try again.';
}

function redactSensitiveData(message: string): string {
  return message
    .replace(/(key|api[_-]?key|token|secret)=([^&\s<]+)/gi, '$1=<redacted>')
    .replace(/Bearer\s+[A-Za-z0-9._~+/-]+=*/gi, 'Bearer <redacted>');
}

export function average(values: number[]): number {
  if (values.length === 0) {
    return 0;
  }
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

export function currency(value: string | number | undefined, currencyCode = 'USD'): string {
  if (typeof value !== 'number') {
    const numericValue = Number(value);
    if (!Number.isFinite(numericValue)) {
      return 'Not available';
    }
    value = numericValue;
  }
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currencyCode,
    maximumFractionDigits: 0,
  }).format(value);
}
