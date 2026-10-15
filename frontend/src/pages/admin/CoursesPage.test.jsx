import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import * as client from "../../api/client.js";
import * as coursesApi from "../../api/courses.js";
import App from "../../App.jsx";
import AuthProvider from "../../auth/AuthProvider.jsx";
import CoursesPage from "./CoursesPage.jsx";

vi.mock("../../api/courses.js");

const departments = [{ id: 1, name: "CSE-AIML", sections: [] }];
const faculty = [{ id: 7, name: "Dr. Asha Rao", email: "faculty1@pes.edu", role: "faculty" }];
const se = {
  id: 10,
  code: "UE24AM241A",
  name: "Software Engineering",
  credits: 4,
  department_id: 1,
  department_name: "CSE-AIML",
  faculty_id: 7,
  faculty_name: "Dr. Asha Rao",
  syllabus: "Unit 1: Requirements & SRS.",
};
const ml = {
  ...se,
  id: 11,
  code: "UE24AM242A",
  name: "Machine Learning",
  faculty_id: null,
  faculty_name: null,
  syllabus: "",
};
const students = [
  { id: 1, srn: "PES1UG24AM001", name: "Student 01", section_name: "H" },
  { id: 2, srn: "PES1UG24AM002", name: "Student 02", section_name: "H" },
];

function apiError(status, error) {
  return { response: { status, data: { error } } };
}

beforeEach(() => {
  coursesApi.listCourses.mockResolvedValue([se, ml]);
  coursesApi.listDepartments.mockResolvedValue(departments);
  coursesApi.listFaculty.mockResolvedValue(faculty);
  coursesApi.listStudents.mockResolvedValue(students);
  coursesApi.listEnrolledStudents.mockResolvedValue([students[0]]);
});

afterEach(() => vi.resetAllMocks());

async function renderPage() {
  render(<CoursesPage />);
  return screen.findByRole("button", { name: "UE24AM241A" });
}

describe("Admin Courses page (issue #11)", () => {
  it("lists courses with department and faculty", async () => {
    await renderPage();
    expect(screen.getByText("Software Engineering")).toBeInTheDocument();
    expect(screen.getByText("Machine Learning")).toBeInTheDocument();
    expect(screen.getByText("Dr. Asha Rao")).toBeInTheDocument();
    expect(screen.getByText("Not assigned")).toBeInTheDocument();
  });

  it("TC-CRS-02: clicking a course shows its syllabus", async () => {
    fireEvent.click(await renderPage());
    expect(await screen.findByText("Unit 1: Requirements & SRS.")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Close" }));
    fireEvent.click(screen.getByRole("button", { name: "UE24AM242A" }));
    expect(await screen.findByText("No syllabus entered yet.")).toBeInTheDocument();
  });

  it("filters the table by code or name", async () => {
    await renderPage();
    const search = screen.getByLabelText("Search courses");

    fireEvent.change(search, { target: { value: "machine" } });
    expect(screen.queryByText("Software Engineering")).not.toBeInTheDocument();
    expect(screen.getByText("Machine Learning")).toBeInTheDocument();

    fireEvent.change(search, { target: { value: "zzz" } });
    expect(screen.getByText("No matching courses.")).toBeInTheDocument();
  });

  it("shows an empty state when there are no courses", async () => {
    coursesApi.listCourses.mockResolvedValue([]);
    render(<CoursesPage />);
    expect(await screen.findByText("No courses yet. Add the first one.")).toBeInTheDocument();
  });

  it("shows an error when the courses cannot be loaded", async () => {
    coursesApi.listCourses.mockRejectedValue(new Error("Network Error"));
    render(<CoursesPage />);
    expect(await screen.findByText(/Cannot reach the server/)).toBeInTheDocument();
  });

  it("adds a course from the pop-up form", async () => {
    const created = { ...se, id: 12, code: "UE24AM243A", name: "DBMS", faculty_id: null };
    coursesApi.createCourse.mockResolvedValue(created);
    await renderPage();

    fireEvent.click(screen.getByRole("button", { name: "Add course" }));
    fireEvent.change(await screen.findByLabelText("Course code"), {
      target: { value: "UE24AM243A" },
    });
    fireEvent.change(screen.getByLabelText("Course name"), { target: { value: "DBMS" } });
    fireEvent.change(screen.getByLabelText("Credits"), { target: { value: "3" } });
    fireEvent.change(screen.getByLabelText("Faculty"), { target: { value: "7" } });
    fireEvent.change(screen.getByLabelText("Syllabus"), { target: { value: "Unit 1: SQL" } });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));

    expect(await screen.findByText("DBMS")).toBeInTheDocument();
    expect(coursesApi.createCourse).toHaveBeenCalledWith({
      code: "UE24AM243A",
      name: "DBMS",
      credits: 3,
      department_id: 1,
      faculty_id: 7,
      syllabus: "Unit 1: SQL",
    });
  });

  it("TC-CRS-01: shows the API's duplicate-code message in the form", async () => {
    coursesApi.createCourse.mockRejectedValue(
      apiError(409, "Course code UE24AM241A already exists."),
    );
    await renderPage();

    fireEvent.click(screen.getByRole("button", { name: "Add course" }));
    fireEvent.change(await screen.findByLabelText("Course code"), {
      target: { value: "UE24AM241A" },
    });
    fireEvent.change(screen.getByLabelText("Course name"), { target: { value: "Copy" } });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));

    expect(await screen.findByText("Course code UE24AM241A already exists.")).toBeInTheDocument();
  });

  it("edits a course", async () => {
    coursesApi.updateCourse.mockResolvedValue({ ...ml, credits: 3, name: "ML" });
    await renderPage();

    fireEvent.click(screen.getByRole("button", { name: "Edit UE24AM242A" }));
    const name = await screen.findByLabelText("Course name");
    expect(name).toHaveValue("Machine Learning");
    fireEvent.change(name, { target: { value: "ML" } });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));

    expect(await screen.findByText("ML")).toBeInTheDocument();
    expect(coursesApi.updateCourse).toHaveBeenCalledWith(
      11,
      expect.objectContaining({ name: "ML", faculty_id: null, department_id: 1 }),
    );
  });

  it("deletes a course only after confirmation", async () => {
    coursesApi.deleteCourse.mockResolvedValue();
    await renderPage();

    fireEvent.click(screen.getByRole("button", { name: "Delete UE24AM242A" }));
    const dialog = await screen.findByRole("dialog");
    expect(coursesApi.deleteCourse).not.toHaveBeenCalled();
    fireEvent.click(within(dialog).getByRole("button", { name: "Delete" }));

    await waitFor(() => expect(screen.queryByText("Machine Learning")).not.toBeInTheDocument());
    expect(coursesApi.deleteCourse).toHaveBeenCalledWith(11);
  });

  it("shows an error if deleting fails", async () => {
    coursesApi.deleteCourse.mockRejectedValue(apiError(404, "Course not found."));
    await renderPage();

    fireEvent.click(screen.getByRole("button", { name: "Delete UE24AM242A" }));
    fireEvent.click(
      within(await screen.findByRole("dialog")).getByRole("button", { name: "Delete" }),
    );
    expect(await screen.findByText("Course not found.")).toBeInTheDocument();
  });
});

describe("Enrollment panel (issue #12)", () => {
  async function openRoster() {
    await renderPage();
    fireEvent.click(screen.getByRole("button", { name: "Students in UE24AM241A" }));
    return screen.findByText("Students enrolled in UE24AM241A – Software Engineering");
  }

  function pickStudents(...labels) {
    const select = screen.getByLabelText("Add students");
    for (const option of select.options) option.selected = labels.includes(option.textContent);
    fireEvent.change(select);
  }

  it("shows the roster and offers only students not yet enrolled", async () => {
    await openRoster();
    expect(await screen.findByRole("button", { name: "Remove PES1UG24AM001" })).toBeInTheDocument();
    const options = Array.from(screen.getByLabelText("Add students").options);
    expect(options.map((option) => option.textContent)).toEqual(["PES1UG24AM002 – Student 02"]);
  });

  it("TC-CRS-03: enrolls the selected students and refreshes the roster", async () => {
    coursesApi.enrollStudents.mockResolvedValue([students[1]]);
    await openRoster();
    await screen.findByRole("button", { name: "Remove PES1UG24AM001" });

    coursesApi.listEnrolledStudents.mockResolvedValue(students);
    pickStudents("PES1UG24AM002 – Student 02");
    fireEvent.click(screen.getByRole("button", { name: "Enroll selected" }));

    expect(await screen.findByText("Enrolled 1 student(s).")).toBeInTheDocument();
    expect(coursesApi.enrollStudents).toHaveBeenCalledWith(10, [2]);
    expect(await screen.findByRole("button", { name: "Remove PES1UG24AM002" })).toBeInTheDocument();
  });

  it("TC-CRS-03: shows the API message for a duplicate enrollment", async () => {
    coursesApi.enrollStudents.mockRejectedValue(
      apiError(409, "PES1UG24AM002 is already enrolled in UE24AM241A."),
    );
    await openRoster();
    await screen.findByRole("button", { name: "Remove PES1UG24AM001" });

    pickStudents("PES1UG24AM002 – Student 02");
    fireEvent.click(screen.getByRole("button", { name: "Enroll selected" }));

    expect(
      await screen.findByText("PES1UG24AM002 is already enrolled in UE24AM241A."),
    ).toBeInTheDocument();
  });

  it("removes a student from the course", async () => {
    coursesApi.removeEnrollment.mockResolvedValue();
    await openRoster();

    coursesApi.listEnrolledStudents.mockResolvedValue([]);
    fireEvent.click(await screen.findByRole("button", { name: "Remove PES1UG24AM001" }));

    expect(await screen.findByText("Removed PES1UG24AM001 from UE24AM241A.")).toBeInTheDocument();
    expect(screen.getByText("No students enrolled yet.")).toBeInTheDocument();
    expect(coursesApi.removeEnrollment).toHaveBeenCalledWith(10, 1);
  });

  it("shows an error if removing fails", async () => {
    coursesApi.removeEnrollment.mockRejectedValue(apiError(404, "Student is not enrolled."));
    await openRoster();
    fireEvent.click(await screen.findByRole("button", { name: "Remove PES1UG24AM001" }));
    expect(await screen.findByText("Student is not enrolled.")).toBeInTheDocument();
  });
});

describe("Routing", () => {
  it("opens the Courses page at /admin/courses for an Admin", async () => {
    vi.spyOn(client, "getMe").mockResolvedValue({ id: 1, name: "Admin", role: "admin" });
    render(
      <MemoryRouter initialEntries={["/admin/courses"]}>
        <AuthProvider>
          <App />
        </AuthProvider>
      </MemoryRouter>,
    );
    expect(
      await screen.findByRole("heading", { name: "Courses & Enrollment" }),
    ).toBeInTheDocument();
  });
});
