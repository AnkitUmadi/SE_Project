import axios from "axios";
import { afterEach, describe, expect, it, vi } from "vitest";
import api, { getMe, login, logout } from "./client.js";

afterEach(() => vi.restoreAllMocks());

// Replace the network layer so no real request is sent; record what would have been sent.
function fakeAdapter(responder) {
  const sent = [];
  api.defaults.adapter = async (config) => {
    sent.push(config);
    return responder(config);
  };
  return sent;
}

describe("API client", () => {
  it("adds the CSRF token header to POST requests (TC-SEC-05)", async () => {
    vi.spyOn(axios, "get").mockResolvedValue({ data: { csrf_token: "tok123" } });
    const sent = fakeAdapter(() => ({ status: 200, data: { user: { role: "admin" } } }));

    const user = await login("a@pes.edu", "pw");

    expect(user.role).toBe("admin");
    expect(sent[0].headers["X-CSRFToken"]).toBe("tok123");
  });

  it("does not fetch a CSRF token for GET requests", async () => {
    const csrf = vi.spyOn(axios, "get");
    fakeAdapter(() => ({ status: 200, data: { user: { role: "student" } } }));

    expect((await getMe()).role).toBe("student");
    expect(csrf).not.toHaveBeenCalled();
  });

  it("getMe returns null when not logged in", async () => {
    fakeAdapter((config) => {
      const error = new Error("401");
      error.response = { status: 401, data: {} };
      error.config = config;
      throw error;
    });
    expect(await getMe()).toBeNull();
  });

  it("logout sends a POST", async () => {
    vi.spyOn(axios, "get").mockResolvedValue({ data: { csrf_token: "t" } });
    const sent = fakeAdapter(() => ({ status: 200, data: {} }));
    await logout();
    expect(sent[0].method).toBe("post");
    expect(sent[0].url).toBe("/auth/logout");
  });
});
