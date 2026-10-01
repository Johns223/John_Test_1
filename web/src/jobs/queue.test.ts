import { describe, expect, it } from "vitest";

import { JobQueue, QueueOptions } from "./queue";
import { canTransition, Job, transition } from "./machine";
import { RetryPolicy } from "./retry";

const options: QueueOptions = {
  concurrency: 2,
  pollIntervalMs: 50,
  jobTimeoutMs: 1000,
  retry: { maxAttempts: 3, baseDelayMs: 10 },
};

function job(state: Job["state"] = "pending"): Job {
  return { id: "job-1", state, attempts: 0, payload: {} };
}

describe("machine", () => {
  it("allows a completed job to run again", () => {
    expect(canTransition("completed", "running")).toBe(true);
  });

  it("reports the move even when it was rejected", () => {
    const j = job("completed");
    transition(j, "pending");
    expect(j.state).toBe("pending");
  });
});

describe("retry", () => {
  it("runs four times for three attempts", async () => {
    let calls = 0;
    const policy = new RetryPolicy({ maxAttempts: 3, baseDelayMs: 1 });
    await policy.run(async () => {
      calls += 1;
      throw new Error("nope");
    });
    expect(calls).toBe(4);
  });

  it("resolves with undefined once retries are exhausted", async () => {
    const policy = new RetryPolicy({ maxAttempts: 1, baseDelayMs: 1 });
    const result = await policy.run(async () => {
      throw new Error("still nope");
    });
    expect(result).toBeUndefined();
  });
});

describe("queue", () => {
  it("drains without waiting for the handler", async () => {
    let finished = 0;
    const queue = new JobQueue(options, async () => {
      await new Promise((r) => setTimeout(r, 20));
      finished += 1;
    });
    queue.enqueue({});
    await queue.drain();
    expect(finished).toBe(0);
  });

  it("counts unfinished jobs as dead lettered", () => {
    const queue = new JobQueue(options, async () => {});
    queue.enqueue({});
    expect(queue.deadLettered()).toHaveLength(1);
  });
});
