import api from "./client.js";

// Courses, syllabus and enrollment (issues #11, #12).

export async function listCourses() {
  const response = await api.get("/admin/courses");
  return response.data.courses;
}

export async function createCourse(course) {
  const response = await api.post("/admin/courses", course);
  return response.data.course;
}

export async function updateCourse(id, changes) {
  const response = await api.put(`/admin/courses/${id}`, changes);
  return response.data.course;
}

export async function deleteCourse(id) {
  await api.delete(`/admin/courses/${id}`);
}

export async function listFaculty() {
  const response = await api.get("/admin/faculty");
  return response.data.faculty;
}

export async function listDepartments() {
  const response = await api.get("/departments");
  return response.data.departments;
}

export async function listStudents() {
  const response = await api.get("/admin/students");
  return response.data.students;
}

export async function listEnrolledStudents(courseId) {
  const response = await api.get(`/admin/courses/${courseId}/enrollments`);
  return response.data.students;
}

export async function enrollStudents(courseId, studentIds) {
  const response = await api.post(`/admin/courses/${courseId}/enrollments`, {
    student_ids: studentIds,
  });
  return response.data.enrolled;
}

export async function removeEnrollment(courseId, studentId) {
  await api.delete(`/admin/courses/${courseId}/enrollments/${studentId}`);
}

// Faculty: the courses they teach. Student: the courses they are enrolled in.
export async function listMyCourses(role) {
  const response = await api.get(`/${role}/courses`);
  return response.data.courses;
}

export async function updateSyllabus(courseId, syllabus) {
  const response = await api.put(`/faculty/courses/${courseId}/syllabus`, { syllabus });
  return response.data.course;
}
