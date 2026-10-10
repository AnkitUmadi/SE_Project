import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import App from "./App.jsx";
import * as client from "./api/client.js";

describe("App", () => {
  it("shows online when the backend health check succeeds", async () => {
    vi.spyOn(client, "getHealth").mockResolvedValue({ status: "ok" });
    render(<App />);
    expect(await screen.findByText(/Backend is online/)).toBeInTheDocument();
  });

  it("shows offline when the backend cannot be reached", async () => {
    vi.spyOn(client, "getHealth").mockRejectedValue(new Error("network"));
    render(<App />);
    expect(await screen.findByText(/Backend is offline/)).toBeInTheDocument();
  });
});
