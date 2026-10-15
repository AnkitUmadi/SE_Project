import { Container, Spinner } from "react-bootstrap";
import { Navigate, Route, Routes } from "react-router-dom";
import AppLayout from "./components/AppLayout.jsx";
import RequireRole from "./components/RequireRole.jsx";
import { HOME_BY_ROLE, useAuth } from "./auth/authContext.js";
import ComingSoonPage from "./pages/ComingSoonPage.jsx";
import HomePage from "./pages/HomePage.jsx";
import LoginPage from "./pages/LoginPage.jsx";
import DepartmentsPage from "./pages/admin/DepartmentsPage.jsx";
import FeesPage from "./pages/admin/FeesPage.jsx";
import StudentsPage from "./pages/admin/StudentsPage.jsx";

// Pages for each role. Add your card's page here (replace its ComingSoonPage).
const PAGES_BY_ROLE = {
  admin: [
    ["departments", <DepartmentsPage key="departments" />],
    ["students", <StudentsPage key="students" />],
    ["fees", <FeesPage key="fees" />],
    ["courses", <ComingSoonPage key="courses" title="Courses & Enrollment" card={11} />],
    ["esa", <ComingSoonPage key="esa" title="ESA Window" card={17} />],
    ["audit", <ComingSoonPage key="audit" title="Audit Log" card={6} />],
  ],
  faculty: [
    ["courses", <ComingSoonPage key="courses" title="My Courses" card={11} />],
    ["attendance", <ComingSoonPage key="attendance" title="Mark Attendance" card={13} />],
    ["marks", <ComingSoonPage key="marks" title="Enter Marks" card={15} />],
    ["reports", <ComingSoonPage key="reports" title="Course Analysis" card={25} />],
  ],
  student: [
    ["courses", <ComingSoonPage key="courses" title="My Courses" card={12} />],
    ["attendance", <ComingSoonPage key="attendance" title="My Attendance" card={21} />],
    ["esa", <ComingSoonPage key="esa" title="ESA Registration" card={18} />],
    ["results", <ComingSoonPage key="results" title="My Results" card={21} />],
  ],
};

export default function App() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <Container className="py-5 text-center">
        <Spinner animation="border" role="status" aria-label="Loading" />
      </Container>
    );
  }

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      {Object.entries(HOME_BY_ROLE).map(([role, path]) => (
        <Route
          key={role}
          path={path}
          element={
            <RequireRole role={role}>
              <AppLayout />
            </RequireRole>
          }
        >
          <Route index element={<HomePage />} />
          {PAGES_BY_ROLE[role].map(([subPath, element]) => (
            <Route key={subPath} path={subPath} element={element} />
          ))}
          <Route path="*" element={<Navigate to={path} replace />} />
        </Route>
      ))}
      <Route
        path="*"
        element={<Navigate to={user ? HOME_BY_ROLE[user.role] : "/login"} replace />}
      />
    </Routes>
  );
}
