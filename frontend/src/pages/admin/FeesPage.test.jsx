import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import * as adminApi from "../../api/admin.js";
import FeesPage from "./FeesPage.jsx";
import { apiError, renderPage, STUDENTS } from "./testUtils.jsx";

beforeEach(() => {
  vi.spyOn(adminApi, "listStudents").mockResolvedValue(STUDENTS);
});
afterEach(() => vi.restoreAllMocks());

const row = (name) => screen.getByText(name).closest("tr");

describe("Fee Status page (F-015, TC-FEE-01)", () => {
  it("opens the semester most students are in and switches semester", async () => {
    const list = vi
      .spyOn(adminApi, "listFees")
      .mockResolvedValue([{ id: 1, student_id: 1, semester: 1, status: "PAID" }]);
    renderPage(<FeesPage />);

    await screen.findByText("Asha Rao");
    // Fees load after the student list, so wait for the badge to appear.
    expect(
      await within(row("Asha Rao")).findByText("Paid", { selector: ".srs-status" }),
    ).toHaveClass("srs-status-paid");
    expect(within(row("Rahul Nair")).getByText("Not set")).toBeInTheDocument();
    expect(list).toHaveBeenCalledWith(3);

    fireEvent.change(screen.getByLabelText("Semester"), { target: { value: "1" } });
    await waitFor(() => expect(list).toHaveBeenCalledWith(1));
  });

  it("marks a student as unpaid", async () => {
    vi.spyOn(adminApi, "listFees").mockResolvedValue([]);
    const setFee = vi.spyOn(adminApi, "setFee").mockResolvedValue({});
    renderPage(<FeesPage />);

    const button = await screen.findByRole("button", { name: "Mark Rahul Nair unpaid" });
    await waitFor(() => expect(adminApi.listFees).toHaveBeenCalled());
    fireEvent.click(button);

    await waitFor(() => expect(setFee).toHaveBeenCalledWith(2, 3, "UNPAID"));
    expect(within(row("Rahul Nair")).getByText("Unpaid", { selector: ".srs-status" })).toHaveClass(
      "srs-status-unpaid",
    );
    expect(
      await screen.findByText("Rahul Nair: semester 3 fees marked unpaid"),
    ).toBeInTheDocument();
  });

  it("filters by status", async () => {
    vi.spyOn(adminApi, "listFees").mockResolvedValue([
      { id: 1, student_id: 1, semester: 1, status: "PAID" },
    ]);
    renderPage(<FeesPage />);

    fireEvent.click(await screen.findByRole("button", { name: "Not set 1" }));
    expect(screen.queryByText("Asha Rao")).not.toBeInTheDocument();
    expect(screen.getByText("Rahul Nair")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Unpaid 0" }));
    expect(screen.getByText("Nobody matches this filter")).toBeInTheDocument();
  });

  it("shows the server's error when saving fails", async () => {
    vi.spyOn(adminApi, "listFees").mockResolvedValue([]);
    vi.spyOn(adminApi, "setFee").mockRejectedValue(apiError(403, "Admin access required."));
    renderPage(<FeesPage />);

    const button = await screen.findByRole("button", { name: "Mark Asha Rao paid" });
    await waitFor(() => expect(adminApi.listFees).toHaveBeenCalled());
    fireEvent.click(button);
    expect(await screen.findByText("Admin access required.")).toBeInTheDocument();
  });
});
