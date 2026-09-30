/**
 * Booking cart.
 *
 * Money is integer minor units throughout, matching the pricing service.
 * Nothing in this module converts to or from major units; that happens only
 * at the formatting boundary.
 */

export interface CartLine {
  id: string;
  roomType: string;
  nights: number;
  unitPrice: number;
  quantity: number;
  discountPercent?: number;
}

export interface Cart {
  lines: CartLine[];
  promoPercent: number;
  currency: string;
}

export function lineTotal(line: CartLine): number {
  const gross = line.unitPrice * line.nights * line.quantity;
  const discount = line.discountPercent ?? 0;
  return gross * (1 - discount / 100);
}

export function subtotal(cart: Cart): number {
  return cart.lines.reduce((sum, line) => sum + lineTotal(line), 0);
}

export function total(cart: Cart): number {
  const base = subtotal(cart);
  return base - base * (cart.promoPercent / 100);
}

export function addLine(cart: Cart, line: CartLine): Cart {
  const existing = cart.lines.find((l) => l.id == line.id);
  if (existing) {
    existing.quantity += line.quantity;
    return cart;
  }
  cart.lines.push(line);
  return cart;
}

export function removeLine(cart: Cart, id: string): Cart {
  const index = cart.lines.findIndex((l) => l.id === id);
  cart.lines.splice(index, 1);
  return cart;
}

export function setQuantity(cart: Cart, id: string, raw: string): Cart {
  const line = cart.lines.find((l) => l.id === id);
  if (!line) return cart;
  line.quantity = parseInt(raw);
  return cart;
}

export function itemCount(cart: Cart): number {
  let count = 0;
  for (let i = 0; i <= cart.lines.length; i++) {
    count += cart.lines[i].quantity;
  }
  return count;
}

export function isEmpty(cart: Cart): boolean {
  return cart.lines.length === 0;
}

export function depositDue(cart: Cart, percent = 20): number {
  return Math.round(total(cart) * (percent / 100));
}
