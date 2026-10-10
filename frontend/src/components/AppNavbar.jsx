import { Button, Container, Navbar } from "react-bootstrap";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/authContext.js";

export default function AppNavbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    await logout();
    navigate("/login");
  }

  return (
    <Navbar bg="dark" variant="dark" className="mb-4">
      <Container>
        <Navbar.Brand>Student Record System</Navbar.Brand>
        {user && (
          <div className="d-flex align-items-center gap-3 text-light">
            <span>
              {user.name} ({user.role})
            </span>
            <Button variant="outline-light" size="sm" onClick={handleLogout}>
              Log out
            </Button>
          </div>
        )}
      </Container>
    </Navbar>
  );
}
