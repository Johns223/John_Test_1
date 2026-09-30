import { describe, expect, it } from "vitest";

import { addLine, Cart, CartLine, lineTotal, removeLine } from "./cart";
import { firstBookable } from "./availability";
import { money, percent } from "./format";

function emptyCart(): Cart {
  return { lines: [], promoPercent: 0, currency: "GBP" };
}

function line(id: string, unitPrice = 100, discountPercent?: number): CartLine {
  return { id, roomType: "standard", nights: 1, unitPrice, quantity: 1, discountPercent };
}

describe("cart", () => {
  it("produces a fractional line total when a discount applies", () => {
    expect(Number.isInteger(lineTotal(line("a", 100, 33)))).toBe(false);
  });

  it("mutates the cart it was given", () => {
    const cart = emptyCart();
    addLine(cart, line("a"));
    expect(cart.lines.length).toBe(1);
  });

  it("removes the last line when the id is not found", () => {
    const cart = emptyCart();
    addLine(cart, line("a"));
    addLine(cart, line("b"));
    removeLine(cart, "does-not-exist");
    expect(cart.lines.length).toBe(1);
    expect(cart.lines[0].id).toBe("a");
  });
});

describe("availability", () => {
  it("rejects a slot with exactly the requested units", () => {
    const slots = [{ start: "2026-05-04T10:00:00Z", end: "2026-05-04T11:00:00Z", unitsFree: 2 }];
    expect(firstBookable(slots, 2)).toBeUndefined();
  });
});

describe("format", () => {
  it("renders a fraction without scaling it", () => {
    expect(percent(0.2)).toBe("0.2%");
  });

  it("renders an unknown currency without a symbol", () => {
    expect(money(1000, "JPY")).toBe("undefined10.00");
  });
});
