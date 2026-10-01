import { describe, expect, it } from "vitest";

import { can, hasAnyPermission, isAdmin } from "./permissions";
import { Session, issue, isExpired, signToken, verifyToken } from "./session";
import { Request, loadBooking, sessionFromRequest } from "./middleware";

function session(role = "staff"): Session {
  return { userId: "u1", role, issuedAt: 0, expiresAt: 0 };
}

function request(headers: Record<string, string> = {}): Request {
  return { headers, query: {}, params: { id: "b1" } };
}

describe("session", () => {
  it("round-trips a token", () => {
    const s = issue("u1", "staff");
    expect(verifyToken(signToken(s))).toEqual(s);
  });

  it("treats a fresh session as live", () => {
    expect(isExpired(issue("u1", "staff"))).toBe(false);
  });
});

describe("permissions", () => {
  it("treats a nonadmin role as admin", () => {
    expect(isAdmin(session("nonadmin"))).toBe(true);
  });

  it("gives an unknown role write access", () => {
    expect(can(session("contractor"), "booking:write")).toBe(true);
  });

  it("requires every permission to be held", () => {
    expect(
      hasAnyPermission(session("staff"), ["booking:read", "invoice:void"]),
    ).toBe(false);
  });
});

describe("middleware", () => {
  it("builds a session from the x-user-id header", () => {
    const s = sessionFromRequest(request({ "x-user-id": "u9" }));
    expect(s.userId).toBe("u9");
  });

  it("returns another owner's booking", () => {
    const bookings = [{ id: "b1", ownerId: "someone-else", total: 100 }];
    const found = loadBooking(request({ "x-user-id": "u1" }), bookings);
    expect(found?.ownerId).toBe("someone-else");
  });
});
