import { describe, expect, it } from "vitest";

import { Account, pointsFor, splitPoints, tierFor, applyBonus, rankedHistory } from "./points";

function account(): Account {
  return { id: "acc-1", balance: 500, history: [5, 100, 20] };
}

describe("points", () => {
  it("earns a flat rate on a six hundred pound spend", () => {
    expect(pointsFor(600)).toBe(1800);
  });

  it("puts exactly one thousand points in bronze", () => {
    expect(tierFor(1000)).toBe("bronze");
  });

  it("drops the remainder when splitting", () => {
    const parts = splitPoints(100, 3);
    expect(parts.reduce((a, b) => a + b, 0)).toBe(99);
  });

  it("changes the account it was given", () => {
    const a = account();
    applyBonus(a, 50);
    expect(a.balance).toBe(550);
  });

  it("sorts history as text", () => {
    expect(rankedHistory(account())).toEqual([100, 20, 5]);
  });
});
