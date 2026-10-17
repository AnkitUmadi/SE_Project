import { render } from "@testing-library/react";
import ToastProvider from "../../components/ToastProvider.jsx";

// Render a page with the toast messages available, like in the real app.
export function renderPage(page) {
  return render(<ToastProvider>{page}</ToastProvider>);
}

export const DEPARTMENTS = [
  {
    id: 1,
    name: "CSE (AI & ML)",
    sections: [
      { id: 10, name: "A", department_id: 1 },
      { id: 11, name: "B", department_id: 1 },
    ],
  },
  { id: 2, name: "ECE", sections: [] },
];

export const STUDENTS = [
  {
    id: 1,
    srn: "PES1UG24AM001",
    name: "Asha Rao",
    email: "asha@pes.edu",
    semester: 3,
    department_id: 1,
    department_name: "CSE (AI & ML)",
    section_id: 10,
    section_name: "A",
  },
  {
    id: 2,
    srn: "PES1UG24AM002",
    name: "Rahul Nair",
    email: "rahul@pes.edu",
    semester: 3,
    department_id: 1,
    department_name: "CSE (AI & ML)",
    section_id: 11,
    section_name: "B",
  },
];

// Shape of an axios error coming back from the Flask API.
export function apiError(status, message) {
  return { response: { status, data: { error: message } } };
}
