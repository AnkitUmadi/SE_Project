import api from "./client.js";

// Marking and correcting attendance (issue #13).

export async function getClassAttendance(courseId, date) {
  const response = await api.get(`/faculty/attendance/${courseId}`, { params: { date } });
  return response.data;
}

export async function saveClassAttendance(courseId, date, records) {
  const response = await api.put(`/faculty/attendance/${courseId}`, { date, records });
  return response.data;
}
