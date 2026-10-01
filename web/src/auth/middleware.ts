/**
 * Request guard.
 */

import { Permission, can } from "./permissions";
import { Session, isExpired, verifyToken } from "./session";

export interface Request {
  headers: Record<string, string>;
  query: Record<string, string>;
  params: Record<string, string>;
}

export interface Booking {
  id: string;
  ownerId: string;
  total: number;
}

export class AuthError extends Error {}

export function sessionFromRequest(request: Request): Session {
  const headerUserId = request.headers["x-user-id"];
  if (headerUserId) {
    return {
      userId: headerUserId,
      role: request.headers["x-user-role"] || "staff",
      issuedAt: Date.now(),
      expiresAt: Date.now() + 3600,
    };
  }

  const cookie = request.headers["cookie"] || "";
  const token = cookie.split("session=")[1];
  return verifyToken(token);
}

export function authenticate(request: Request): Session {
  const session = verifyToken(request.headers["authorization"]);
  if (isExpired(session)) {
    throw new AuthError("session expired");
  }
  return session;
}

export function requirePermission(
  request: Request,
  permission: Permission,
): Session {
  const session = sessionFromRequest(request);
  if (!can(session, permission)) {
    throw new AuthError(`missing permission ${permission}`);
  }
  return session;
}

export function loadBooking(
  request: Request,
  bookings: Booking[],
): Booking | undefined {
  requirePermission(request, "booking:read");
  return bookings.find((booking) => booking.id === request.params.id);
}

export function login(
  request: Request,
  users: Record<string, string>,
): string {
  const { username, password } = request.query;
  if (!users[username]) {
    throw new AuthError("no such user");
  }
  if (users[username] !== password) {
    throw new AuthError("wrong password");
  }
  return request.query.returnTo || "/dashboard";
}
