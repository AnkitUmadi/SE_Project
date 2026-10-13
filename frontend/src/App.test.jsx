import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "./App.jsx";
import AuthProvider from "./auth/AuthProvider.jsx";
import * as client from "./api/client.js";

// Render the whole app at a given URL, with the backend calls faked.
function renderApp(path = "/") {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <AuthProvider>
        <App />
      </AuthProvider>
    </MemoryRouter>,
  );
}

const admin = { id: 1, email: "admin@pes.edu", name: "Admin User", role: "admin" };
const faculty = { id: 2, email: "f1@pes.edu", name: "Faculty One", role: "faculty" };
const student = { id: 3, email: "s1@pes.edu", name: "Student One", role: "student" };

afterEach(() => vi.restoreAllMocks());

describe("App routing and login (TC-AUTH-01/02/04)", () => {
  it("shows the login page when nobody is logged in", async () => {
    vi.spyOn(client, "getMe").mockResolvedValue(null);
    renderApp("/admin");
    expect(await screen.findByRole("heading", { name: "Log in" })).toBeInTheDocument();
  });

  it("logs in and opens the role's home page", async () => {
    vi.spyOn(client, "getMe").mockResolvedValue(null);
    vi.spyOn(client, "login").mockResolvedValue(admin);
    renderApp("/login");

    fireEvent.change(await screen.findByLabelText("Email"), { target: { value: "admin@pes.edu" } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "Secret#123" } });
    fireEvent.click(screen.getByRole("button", { name: "Log in" }));

    expect(await screen.findByText("Admin dashboard")).toBeInTheDocument();
    expect(client.login).toHaveBeenCalledWith("admin@pes.edu", "Secret#123");
  });

  it("shows the server's error message on a wrong password", async () => {
    vi.spyOn(client, "getMe").mockResolvedValue(null);
    vi.spyOn(client, "login").mockRejectedValue({
      response: { status: 401, data: { error: "Invalid email or password." } },
    });
    renderApp("/login");

    fireEvent.change(await screen.findByLabelText("Email"), { target: { value: "admin@pes.edu" } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "wrong" } });
    fireEvent.click(screen.getByRole("button", { name: "Log in" }));

    expect(await screen.findByText("Invalid email or password.")).toBeInTheDocument();
  });

  it("explains when the backend cannot be reached", async () => {
    vi.spyOn(client, "getMe").mockResolvedValue(null);
    vi.spyOn(client, "login").mockRejectedValue(new Error("Network Error"));
    renderApp("/login");

    fireEvent.change(await screen.findByLabelText("Email"), { target: { value: "a@pes.edu" } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "x" } });
    fireEvent.click(screen.getByRole("button", { name: "Log in" }));

    expect(await screen.findByText(/Cannot reach the server/)).toBeInTheDocument();
  });

  it("sends a student who opens /admin to the student home page", async () => {
    vi.spyOn(client, "getMe").mockResolvedValue(student);
    renderApp("/admin");
    expect(await screen.findByText("Student dashboard")).toBeInTheDocument();
  });

  it("logs out and returns to the login page", async () => {
    vi.spyOn(client, "getMe").mockResolvedValue(admin);
    vi.spyOn(client, "logout").mockResolvedValue();
    renderApp("/admin");

    fireEvent.click(await screen.findByRole("button", { name: "Log out" }));
    expect(await screen.findByRole("heading", { name: "Log in" })).toBeInTheDocument();
  });
});

describe("Role-based menus and route guards (TC-AUTH-03)", () => {
  it("shows only Student menu items when logged in as Student", async () => {
    vi.spyOn(client, "getMe").mockResolvedValue(student);
    renderApp("/student");

    expect(await screen.findByText("Student dashboard")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "My Attendance" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "ESA Registration" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "My Results" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Audit Log" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Enter Marks" })).not.toBeInTheDocument();
  });

  it("shows only Faculty menu items when logged in as Faculty", async () => {
    vi.spyOn(client, "getMe").mockResolvedValue(faculty);
    renderApp("/faculty");

    expect(await screen.findByText("Faculty dashboard")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Mark Attendance" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Enter Marks" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Audit Log" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "My Results" })).not.toBeInTheDocument();
  });

  it("shows only Admin menu items when logged in as Admin", async () => {
    vi.spyOn(client, "getMe").mockResolvedValue(admin);
    renderApp("/admin");

    expect(await screen.findByText("Admin dashboard")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Students" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Fee Status" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Audit Log" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Enter Marks" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "My Results" })).not.toBeInTheDocument();
  });

  it("redirects a student away from faculty or admin sub-routes", async () => {
    vi.spyOn(client, "getMe").mockResolvedValue(student);
    renderApp("/faculty/marks");
    expect(await screen.findByText("Student dashboard")).toBeInTheDocument();
  });
});
