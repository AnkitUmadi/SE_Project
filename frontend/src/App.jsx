import { Container, Spinner } from "react-bootstrap";
import { Navigate, Route, Routes } from "react-router-dom";
import AppNavbar from "./components/AppNavbar.jsx";
import RequireRole from "./components/RequireRole.jsx";
import { HOME_BY_ROLE, useAuth } from "./auth/authContext.js";
import HomePage from "./pages/HomePage.jsx";
import LoginPage from "./pages/LoginPage.jsx";

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
    <>
      <AppNavbar />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        {Object.entries(HOME_BY_ROLE).map(([role, path]) => (
          <Route
            key={role}
            path={`${path}/*`}
            element={
              <RequireRole role={role}>
                <HomePage />
              </RequireRole>
            }
          />
        ))}
        <Route
          path="*"
          element={<Navigate to={user ? HOME_BY_ROLE[user.role] : "/login"} replace />}
        />
      </Routes>
    </>
  );
}
