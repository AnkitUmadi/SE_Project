import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import * as adminApi from "../../api/admin.js";
import DepartmentsPage from "./DepartmentsPage.jsx";
import { apiError, DEPARTMENTS, renderPage } from "./testUtils.jsx";

afterEach(() => vi.restoreAllMocks());

describe("Departments & Sections page (F-004)", () => {
  it("lists departments with their sections", async () => {
    vi.spyOn(adminApi, "listDepartments").mockResolvedValue(DEPARTMENTS);
    renderPage(<DepartmentsPage />);

    const cse = await screen.findByRole("article", { name: "CSE (AI & ML)" });
    expect(within(cse).getByText("2 sections")).toBeInTheDocument();
    expect(within(cse).getByText("A")).toBeInTheDocument();
    expect(within(screen.getByRole("article", { name: "ECE" })).getByText("No sections yet."));
  });

  it("shows an empty state when there are no departments", async () => {
    vi.spyOn(adminApi, "listDepartments").mockResolvedValue([]);
    renderPage(<DepartmentsPage />);
    expect(await screen.findByText("No departments yet")).toBeInTheDocument();
  });

  it("adds a department", async () => {
    const list = vi.spyOn(adminApi, "listDepartments").mockResolvedValue([]);
    const create = vi.spyOn(adminApi, "createDepartment").mockResolvedValue({ id: 3 });
    renderPage(<DepartmentsPage />);

    fireEvent.click(await screen.findByRole("button", { name: "Add department" }));
    fireEvent.change(screen.getByLabelText("Department name"), { target: { value: "ME" } });
    fireEvent.click(
      within(screen.getByRole("dialog")).getByRole("button", { name: "Add department" }),
    );

    await waitFor(() => expect(create).toHaveBeenCalledWith("ME"));
    expect(await screen.findByText("Department ME added")).toBeInTheDocument();
    expect(list).toHaveBeenCalledTimes(2);
  });

  it("shows the server's error when the department already exists", async () => {
    vi.spyOn(adminApi, "listDepartments").mockResolvedValue(DEPARTMENTS);
    vi.spyOn(adminApi, "createDepartment").mockRejectedValue(
      apiError(409, "Department already exists."),
    );
    renderPage(<DepartmentsPage />);

    fireEvent.click(await screen.findByRole("button", { name: "Add department" }));
    fireEvent.change(screen.getByLabelText("Department name"), { target: { value: "ECE" } });
    fireEvent.click(
      within(screen.getByRole("dialog")).getByRole("button", { name: "Add department" }),
    );

    expect(await screen.findByText("Department already exists.")).toBeInTheDocument();
  });

  it("adds a section to a department", async () => {
    vi.spyOn(adminApi, "listDepartments").mockResolvedValue(DEPARTMENTS);
    const create = vi.spyOn(adminApi, "createSection").mockResolvedValue({ id: 12 });
    renderPage(<DepartmentsPage />);

    const ece = await screen.findByRole("article", { name: "ECE" });
    fireEvent.change(within(ece).getByLabelText("New section name for ECE"), {
      target: { value: "C" },
    });
    fireEvent.click(within(ece).getByRole("button", { name: "Add section" }));

    await waitFor(() => expect(create).toHaveBeenCalledWith(2, "C"));
    expect(await screen.findByText("Section C added to ECE")).toBeInTheDocument();
  });

  it("asks before removing a section, then removes it", async () => {
    vi.spyOn(adminApi, "listDepartments").mockResolvedValue(DEPARTMENTS);
    const remove = vi.spyOn(adminApi, "deleteSection").mockResolvedValue();
    renderPage(<DepartmentsPage />);

    fireEvent.click(await screen.findByRole("button", { name: "Remove section B" }));
    expect(screen.getByText("Section B will be removed from CSE (AI & ML).")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Remove section" }));

    await waitFor(() => expect(remove).toHaveBeenCalledWith(11));
  });

  it("deletes a department after confirmation", async () => {
    vi.spyOn(adminApi, "listDepartments").mockResolvedValue(DEPARTMENTS);
    const remove = vi.spyOn(adminApi, "deleteDepartment").mockResolvedValue();
    renderPage(<DepartmentsPage />);

    fireEvent.click(await screen.findByRole("button", { name: "Delete ECE" }));
    fireEvent.click(screen.getByRole("button", { name: "Delete department" }));

    await waitFor(() => expect(remove).toHaveBeenCalledWith(2));
    expect(await screen.findByText("Department ECE deleted")).toBeInTheDocument();
  });

  it("explains when the server cannot be reached", async () => {
    vi.spyOn(adminApi, "listDepartments").mockRejectedValue(new Error("Network Error"));
    renderPage(<DepartmentsPage />);
    expect(await screen.findByText(/Cannot reach the server/)).toBeInTheDocument();
  });
});
