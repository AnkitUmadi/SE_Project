import axios from "axios";
import { afterEach, describe, expect, it, vi } from "vitest";
import * as attendanceApi from "./attendance.js";
import api from "./client.js";
import * as coursesApi from "./courses.js";

afterEach(() => vi.restoreAllMocks());

// Record each request instead of sending it, and answer with `data`.
function fakeAdapter(data) {
  const sent = [];
  vi.spyOn(axios, "get").mockResolvedValue({ data: { csrf_token: "tok" } });
  api.defaults.adapter = async (config) => {
    sent.push({
      method: config.method,
      url: config.url,
      params: config.params,
      body: config.data ? JSON.parse(config.data) : undefined,
    });
    return { status: 200, data };
  };
  return sent;
}

describe("Courses and attendance API calls match the Flask routes", () => {
  it.each([
    [() => coursesApi.listCourses(), "get", "/admin/courses", { courses: [] }],
    [() => coursesApi.createCourse({ code: "X" }), "post", "/admin/courses", { course: {} }],
    [() => coursesApi.updateCourse(3, { name: "Y" }), "put", "/admin/courses/3", { course: {} }],
    [() => coursesApi.deleteCourse(3), "delete", "/admin/courses/3", {}],
    [() => coursesApi.listFaculty(), "get", "/admin/faculty", { faculty: [] }],
    [() => coursesApi.listDepartments(), "get", "/departments", { departments: [] }],
    [() => coursesApi.listStudents(), "get", "/admin/students", { students: [] }],
    [
      () => coursesApi.listEnrolledStudents(3),
      "get",
      "/admin/courses/3/enrollments",
      { students: [] },
    ],
    [() => coursesApi.removeEnrollment(3, 9), "delete", "/admin/courses/3/enrollments/9", {}],
    [() => coursesApi.listMyCourses("student"), "get", "/student/courses", { courses: [] }],
  ])("%#: sends %s to the right URL", async (call, method, url, data) => {
    const sent = fakeAdapter(data);
    await call();
    expect(sent[0].method).toBe(method);
    expect(sent[0].url).toBe(url);
  });

  it("sends the enrollment and syllabus bodies the API expects", async () => {
    const sent = fakeAdapter({ enrolled: [], course: {} });
    await coursesApi.enrollStudents(3, [1, 2]);
    await coursesApi.updateSyllabus(3, "Unit 1");
    expect(sent[0]).toMatchObject({
      method: "post",
      url: "/admin/courses/3/enrollments",
      body: { student_ids: [1, 2] },
    });
    expect(sent[1]).toMatchObject({
      method: "put",
      url: "/faculty/courses/3/syllabus",
      body: { syllabus: "Unit 1" },
    });
  });

  it("reads and saves attendance for a course and date", async () => {
    const sent = fakeAdapter({ recorded: false, students: [] });
    await attendanceApi.getClassAttendance(3, "2026-10-12");
    await attendanceApi.saveClassAttendance(3, "2026-10-12", [{ student_id: 1, present: true }]);
    expect(sent[0]).toMatchObject({
      method: "get",
      url: "/faculty/attendance/3",
      params: { date: "2026-10-12" },
    });
    expect(sent[1]).toMatchObject({
      method: "put",
      url: "/faculty/attendance/3",
      body: { date: "2026-10-12", records: [{ student_id: 1, present: true }] },
    });
  });
});
