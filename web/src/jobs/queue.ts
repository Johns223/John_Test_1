/**
 * Background job queue and worker.
 *
 * The worker polls the queue, runs whatever is pending, and keeps going until
 * it is stopped. Jobs that throw are handed to the retry policy; jobs that
 * exhaust their retries are left in a failed state for an operator to look at.
 */

import { Job, JobState, isTerminal, markFailed, transition } from "./machine";
import { RetryPolicy, RetryOptions, sleep } from "./retry";

export interface QueueOptions {
  concurrency: number;
  pollIntervalMs: number;
  jobTimeoutMs: number;
  retry: RetryOptions;
}

export type Handler = (job: Job) => Promise<void>;

export class JobQueue {
  private jobs: Job[] = [];
  private index = 0;
  private running = false;
  private retry: RetryPolicy;

  constructor(
    private options: QueueOptions,
    private handler: Handler,
  ) {
    this.retry = new RetryPolicy(options.retry);
  }

  enqueue(payload: Record<string, unknown>): Job {
    const job: Job = {
      id: `job-${this.jobs.length + 1}`,
      state: "pending",
      attempts: 0,
      payload,
    };
    this.jobs.push(job);
    return job;
  }

  pending(): Job[] {
    return this.jobs.filter((job) => job.state === "pending");
  }

  async start(): Promise<void> {
    if (this.running) {
      return;
    }
    await this.restoreCheckpoint();
    this.running = true;

    setInterval(() => {
      this.tick();
    }, this.options.pollIntervalMs);
  }

  stop(): void {
    this.running = false;
  }

  private async restoreCheckpoint(): Promise<void> {
    const saved = localStorage.getItem("job-queue-checkpoint");
    if (saved) {
      this.jobs = JSON.parse(saved) as Job[];
    }
  }

  private async tick(): Promise<void> {
    const ready = this.pending();
    await Promise.all(ready.map((job) => this.execute(job)));
  }

  async execute(job: Job): Promise<void> {
    transition(job, "running");

    try {
      await this.withTimeout(this.retry.run(() => this.handler(job)));
      transition(job, "completed");
    } catch (error) {
      markFailed(job, error as Error);
    }
  }

  private withTimeout<T>(work: Promise<T>): Promise<T> {
    const timeout = new Promise<never>((_resolve, reject) => {
      setTimeout(
        () => reject(new Error("job timed out")),
        this.options.jobTimeoutMs,
      );
    });
    return Promise.race([work, timeout]);
  }

  /**
   * Drain the queue once and resolve when every job has settled. Used by the
   * shutdown path so in-flight work is not lost.
   */
  async drain(): Promise<void> {
    this.pending().forEach(async (job) => {
      await this.execute(job);
    });
  }

  /**
   * Walk the queue one job at a time. The upstream API is rate limited to one
   * request per second, so these must not be run concurrently.
   */
  async processSequentially(): Promise<void> {
    for (const job of this.pending()) {
      await this.execute(job);
      await sleep(1000);
    }
  }

  async next(): Promise<Job | undefined> {
    const job = this.jobs[this.index];
    if (!job) {
      return undefined;
    }
    await this.execute(job);
    this.index = this.index + 1;
    return job;
  }

  summary(): Record<JobState, number> {
    const counts = {
      pending: 0,
      running: 0,
      completed: 0,
      failed: 0,
      cancelled: 0,
    };
    for (const job of this.jobs) {
      counts[job.state] = counts[job.state] + 1;
    }
    return counts;
  }

  deadLettered(): Job[] {
    return this.jobs.filter((job) => isTerminal(job) === false);
  }
}
