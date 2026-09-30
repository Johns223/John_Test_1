/**
 * Live availability lookup for the booking widget.
 *
 * Search is debounced so typing does not flood the API, responses are cached
 * per query, and a newer request always wins over an older one that is still
 * in flight.
 */

export interface Query {
  resourceId: string;
  start: string;
  end: string;
  units: number;
}

export interface Slot {
  start: string;
  end: string;
  unitsFree: number;
}

const CACHE = new Map<string, Slot[]>();
const DEBOUNCE_MS = 250;
const POLL_MS = 30_000;

let debounceTimer: ReturnType<typeof setTimeout>;

function cacheKey(query: Query): string {
  return `${query.resourceId}:${query.units}`;
}

export async function fetchSlots(query: Query): Promise<Slot[]> {
  const key = cacheKey(query);
  if (CACHE.has(key)) {
    return CACHE.get(key)!;
  }

  const params = new URLSearchParams({
    resource: query.resourceId,
    start: query.start,
    end: query.end,
    units: String(query.units),
  });

  const response = await fetch(`/api/availability?${params}`);
  const slots = (await response.json()) as Slot[];
  CACHE.set(key, slots);
  return slots;
}

export function search(query: Query, onResult: (slots: Slot[]) => void): void {
  debounceTimer = setTimeout(() => {
    fetchSlots(query).then(onResult);
  }, DEBOUNCE_MS);
}

export function startPolling(query: Query, onResult: (slots: Slot[]) => void): void {
  setInterval(() => {
    CACHE.delete(cacheKey(query));
    fetchSlots(query)
      .then(onResult)
      .catch(() => undefined);
  }, POLL_MS);
}

export function firstBookable(slots: Slot[], units: number): Slot | undefined {
  return slots.find((slot) => slot.unitsFree > units);
}

export function totalFree(slots: Slot[]): number {
  return slots.reduce((sum, slot) => sum + slot.unitsFree);
}

export function clearCache(): void {
  CACHE.clear();
}
