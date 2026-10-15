import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import * as coursesApi from "../api/courses.js";
import { AuthContext } from "../auth/authContext.js";
import MyCoursesPage from "./MyCoursesPage.jsx";

vi.mock("../api/courses.js");

const course = {
  id: 10,
  code: "UE24AM241A",
  name: "Software Engineering",
  credits: 4,
  faculty_name: "Dr. Asha Rao",
  syllabus: "Unit 1: Requirements & SRS.",
};

function renderAs(role) {
  return render(
    <AuthContext.Provider value={{ user: { id: 1, name: "Someone", role } }}>
      <MyCoursesPage />
    </AuthContext.Provider>,
  );
}

afterEach(() => vi.resetAllMocks());

describe("My Courses page (SRS-F-009)", () => {
  it("TC-CRS-02: a student opens an enrolled course and sees its syllabus", async () => {
    coursesApi.listMyCourses.mockResolvedValue([course]);
    renderAs("student");

    fireEvent.click(await screen.findByText(/UE24AM241A – Software Engineering/));
    expect(screen.getByText("Unit 1: Requirements & SRS.")).toBeInTheDocument();
    expect(screen.getByText("Faculty: Dr. Asha Rao")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Edit syllabus" })).not.toBeInTheDocument();
    expect(coursesApi.listMyCourses).toHaveBeenCalledWith("student");
  });

  it("the assigned faculty member edits the syllabus", async () => {
    coursesApi.listMyCourses.mockResolvedValue([{ ...course, syllabus: "" }]);
    coursesApi.updateSyllabus.mockResolvedValue({ ...course, syllabus: "Unit 1: New" });
    renderAs("faculty");

    fireEvent.click(await screen.findByText(/UE24AM241A – Software Engineering/));
    expect(screen.getByText("No syllabus entered yet.")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Edit syllabus" }));
    fireEvent.change(screen.getByLabelText("Syllabus for UE24AM241A"), {
      target: { value: "Unit 1: New" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save syllabus" }));

    expect(await screen.findByRole("button", { name: "Edit syllabus" })).toBeInTheDocument();
    expect(screen.getByText("Unit 1: New")).toBeInTheDocument();
    expect(coursesApi.updateSyllabus).toHaveBeenCalledWith(10, "Unit 1: New");
  });

  it("keeps the editor open and shows the error if saving fails", async () => {
    coursesApi.listMyCourses.mockResolvedValue([course]);
    coursesApi.updateSyllabus.mockRejectedValue({
      response: { status: 403, data: { error: "Only the assigned faculty can edit." } },
    });
    renderAs("faculty");

    fireEvent.click(await screen.findByText(/UE24AM241A/));
    fireEvent.click(screen.getByRole("button", { name: "Edit syllabus" }));
    fireEvent.click(screen.getByRole("button", { name: "Save syllabus" }));
    expect(await screen.findByText("Only the assigned faculty can edit.")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(screen.getByRole("button", { name: "Edit syllabus" })).toBeInTheDocument();
  });

  it("shows empty states for each role", async () => {
    coursesApi.listMyCourses.mockResolvedValue([]);
    renderAs("student");
    expect(await screen.findByText("You are not enrolled in any courses yet.")).toBeInTheDocument();
  });

  it("shows an error when courses cannot be loaded", async () => {
    coursesApi.listMyCourses.mockRejectedValue(new Error("Network Error"));
    renderAs("faculty");
    expect(await screen.findByText(/Cannot reach the server/)).toBeInTheDocument();
  });
});
