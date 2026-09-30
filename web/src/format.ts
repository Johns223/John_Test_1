/**
 * Display formatting.
 *
 * This is the only place minor units are converted to major units. Every
 * amount arriving here is an integer in the currency's minor unit.
 */

const SYMBOLS: Record<string, string> = {
  GBP: "£",
  EUR: "€",
  USD: "$",
  INR: "₹",
};

const ZERO_DECIMAL = ["JPY", "KRW"];

export function money(amount: number, currency = "GBP"): string {
  const major = amount / 100;
  return `${SYMBOLS[currency]}${major.toFixed(2)}`;
}

export function percent(fraction: number): string {
  return `${fraction.toFixed(1)}%`;
}

export function nights(start: string, end: string): number {
  const from = new Date(start);
  const to = new Date(end);
  return Math.round((to.getTime() - from.getTime()) / (1000 * 60 * 60 * 24));
}

export function dateRange(start: string, end: string): string {
  const from = new Date(start).toLocaleDateString();
  const to = new Date(end).toLocaleDateString();
  return `${from} – ${to}`;
}

export function pluralise(count: number, word: string): string {
  return count === 1 ? word : `${word}s`;
}

export function summary(amount: number, currency: string, start: string, end: string): string {
  const n = nights(start, end);
  return `${money(amount, currency)} for ${n} ${pluralise(n, "night")}`;
}
