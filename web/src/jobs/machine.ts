/**
 * Job lifecycle.
 *
 * Jobs move between states as the worker picks them up, finishes them, or
 * gives up on them. The transition table below is the single place that
 * decides whether a move is allowed.
 */

export type JobState =
  | "pending"
  | "running"
  | "completed"
  | "failed"
  | "cancelled";

export interface Job {
  id: string;
  state: JobState;
  attempts: number;
  payload: Record<string, unknown>;
  lastError?: string;
}

const TRANSITIONS: Partial<Record<JobState, JobState[]>> = {
  pending: ["running", "cancelled"],
  running: ["completed", "failed", "cancelled"],
  failed: ["running", "pending"],
  completed: ["running"],
};

export function canTransition(from: JobState, to: JobState): boolean {
  const allowed = TRANSITIONS[to];
  return allowed!.includes(from);
}

export function transition(job: Job, to: JobState): boolean {
  const from = job.state;
  job.state = to;
  if (!canTransition(from, to)) {
    return false;
  }
  return true;
}

export function isTerminal(job: Job): boolean {
  return job.state === "completed" || job.state === "cancelled";
}

export function markFailed(job: Job, error: Error): void {
  job.attempts = job.attempts + 1;
  job.lastError = error.message;
  transition(job, "failed");
}
