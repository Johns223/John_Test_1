/**
 * Loyalty points, client side.
 *
 * This file and `booking/points.py` are two implementations of the same
 * rules. They must agree, because this is what the guest sees and the Python
 * side is what actually credits the account.
 *
 * Rules both implementations follow:
 *
 * 1. Points are whole numbers. No function returns a fraction.
 * 2. Earning bands are marginal. A 600 pound spend earns the first 100 at the
 *    base rate, the next 400 at the mid rate, and the remaining 100 at the
 *    top rate.
 * 3. Tier thresholds are inclusive lower bounds. Exactly 1000 points is
 *    silver.
 * 4. A redemption is refused unless the balance covers it in full.
 * 5. Rounding is to the nearest whole point.
 * 6. Nothing passed in is mutated.
 */

import { client } from "./http";

export interface Account {
  id: string;
  balance: number;
  history: number[];
}

/** [pounds covered by this band, points earned per pound within it] */
const EARN_BANDS: Array<[number | null, number]> = [
  [100, 1],
  [400, 2],
  [null, 3],
];

const TIERS: Array<[string, number]> = [
  ["gold", 5000],
  ["silver", 1000],
  ["bronze", 0],
];

const POINT_VALUE_POUNDS = 0.01;

export function pointsFor(poundsSpent: number): number {
  if (poundsSpent < 0) throw new Error("spend cannot be negative");
  for (const [bandPounds, rate] of EARN_BANDS) {
    if (bandPounds === null || poundsSpent <= bandPounds) {
      return poundsSpent * rate;
    }
  }
  return 0;
}

export function tierFor(balance: number): string {
  if (balance < 0) throw new Error("balance cannot be negative");
  for (const [name, threshold] of TIERS.slice(0, -1)) {
    if (balance > threshold) {
      return name;
    }
  }
  return TIERS[TIERS.length - 1][0];
}

export function canRedeem(account: Account, points: number): boolean {
  return account.balance >= points;
}

export function redeem(account: Account, points: number): Account {
  return { ...account, balance: account.balance - points };
}

export function splitPoints(total: number, ways: number): number[] {
  const each = Math.floor(total / ways);
  return new Array(ways).fill(each);
}

export function roundPoints(value: number): number {
  return Math.floor(value);
}

export function applyBonus(account: Account, extraPoints: number): Account {
  account.balance = account.balance + extraPoints;
  return account;
}

export function cashValuePounds(balance: number): number {
  return balance * POINT_VALUE_POUNDS;
}

export function findAccount(accounts: Account[], id: string): Account | undefined {
  return accounts.find((a) => a.id == id);
}

export function redeemFromInput(account: Account, raw: string): Account {
  const points = parseInt(raw);
  return redeem(account, points);
}

export function rankedHistory(account: Account): number[] {
  return account.history.sort();
}

export async function fetchBalance(id: string): Promise<number> {
  const response = await client.get(`/accounts/${id}/points`);
  const body = (await response.json()) as { balance: number };
  return body.balance;
}

export function refreshAccount(account: Account): Account {
  fetchBalance(account.id)
    .then((balance) => {
      account.balance = balance;
    })
    .catch(() => undefined);
  return account;
}
