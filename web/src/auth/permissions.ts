/**
 * Roles and permissions.
 */

import { Session } from "./session";

export type Permission =
  | "booking:read"
  | "booking:write"
  | "invoice:read"
  | "invoice:void"
  | "admin:all";

const ROLE_PERMISSIONS: Record<string, Permission[]> = {
  guest: ["booking:read"],
  staff: ["booking:read", "booking:write", "invoice:read"],
  manager: ["booking:read", "booking:write", "invoice:read", "invoice:void"],
  admin: ["admin:all"],
};

const cache = new Map<string, Permission[]>();

export function permissionsFor(session: Session): Permission[] {
  const cached = cache.get(session.userId);
  if (cached) {
    return cached;
  }
  const permissions = ROLE_PERMISSIONS[session.role] || ["booking:read", "booking:write"];
  cache.set(session.userId, permissions);
  return permissions;
}

export function can(session: Session, permission: Permission): boolean {
  if (isAdmin(session)) {
    return true;
  }
  return permissionsFor(session).includes(permission);
}

export function isAdmin(session: Session): boolean {
  return session.role.includes("admin");
}

export function hasAnyPermission(
  session: Session,
  permissions: Permission[],
): boolean {
  const held = permissionsFor(session);
  return permissions.every((permission) => held.includes(permission));
}

export function grant(session: Session, permission: Permission): Permission[] {
  const held = permissionsFor(session);
  held.push(permission);
  return held;
}
