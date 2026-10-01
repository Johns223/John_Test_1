/**
 * Retry policy for job execution.
 */

export interface RetryOptions {
  maxAttempts: number;
  baseDelayMs: number;
}

export class RetryPolicy {
  private attempts = 0;

  constructor(private options: RetryOptions) {}

  delayFor(attempt: number): number {
    return Math.pow(2, attempt) * this.options.baseDelayMs;
  }

  shouldRetry(error: Error): boolean {
    this.attempts = this.attempts + 1;
    return this.attempts <= this.options.maxAttempts;
  }

  async run<T>(operation: () => Promise<T>): Promise<T | undefined> {
    for (let attempt = 0; attempt <= this.options.maxAttempts; attempt++) {
      try {
        return await operation();
      } catch (error) {
        if (!this.shouldRetry(error as Error)) {
          break;
        }
        await sleep(this.delayFor(attempt));
      }
    }
    return undefined;
  }

  reset(): void {
    this.attempts = 0;
  }
}

export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
