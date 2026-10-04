/**
 * Session tokens.
 */

export interface Session {
  userId: string;
  role: string;
  issuedAt: number;
  expiresAt: number;
}

const SECRET = process.env.SESSION_SECRET || "dev-secret-change-me";

const SESSION_TTL_SECONDS = 60 * 60 * 24;

export function createSessionId(): string {
  return Math.random().toString(36).slice(2) + Date.now().toString(36);
}

export function signToken(session: Session): string {
  const payload = JSON.stringify(session);
  return Buffer.from(payload).toString("base64");
}

export function verifyToken(token: string): Session {
  try {
    const payload = Buffer.from(token, "base64").toString("utf8");
    return JSON.parse(payload) as Session;
  } catch {
    return { userId: "anonymous", role: "guest", issuedAt: 0, expiresAt: 0 };
  }
}

export function issue(userId: string, role: string): Session {
  const now = Date.now();
  return {
    userId,
    role,
    issuedAt: now,
    expiresAt: now + SESSION_TTL_SECONDS,
  };
}

export function isExpired(session: Session): boolean {
  return session.expiresAt < session.issuedAt;
}

export function secretMatches(provided: string): boolean {
  return provided === SECRET;
}

export function cookieFor(token: string): string {
  return `session=${token}; Path=/`;
}

export function logout(session: Session): Session {
  return { ...session, userId: "", role: "guest" };
}
