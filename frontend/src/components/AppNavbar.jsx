import { Button, Container, Nav, Navbar } from "react-bootstrap";
import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/authContext.js";

const MENU_ITEMS_BY_ROLE = {
  admin: [
    { label: "Dashboard", path: "/admin" },
    { label: "Departments & Sections", path: "/admin/departments" },
    { label: "Students", path: "/admin/students" },
    { label: "Courses & Enrollment", path: "/admin/courses" },
    { label: "Fee Status", path: "/admin/fees" },
    { label: "ESA Window", path: "/admin/esa" },
    { label: "Audit Log", path: "/admin/audit" },
  ],
  faculty: [
    { label: "Dashboard", path: "/faculty" },
    { label: "My Courses", path: "/faculty/courses" },
    { label: "Mark Attendance", path: "/faculty/attendance" },
    { label: "Enter Marks", path: "/faculty/marks" },
    { label: "Course Analysis", path: "/faculty/reports" },
  ],
  student: [
    { label: "Dashboard", path: "/student" },
    { label: "My Courses", path: "/student/courses" },
    { label: "My Attendance", path: "/student/attendance" },
    { label: "ESA Registration", path: "/student/esa" },
    { label: "My Results", path: "/student/results" },
  ],
};

export default function AppNavbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const menuItems = user ? MENU_ITEMS_BY_ROLE[user.role] || [] : [];

  async function handleLogout() {
    await logout();
    navigate("/login");
  }

  return (
    <Navbar bg="dark" variant="dark" expand="lg" className="mb-4">
      <Container>
        <Navbar.Brand>Student Record System</Navbar.Brand>
        {user && (
          <>
            <Nav className="me-auto" aria-label="Role navigation">
              {menuItems.map((item) => (
                <Nav.Link
                  key={item.path}
                  as={NavLink}
                  to={item.path}
                  end={item.path.split("/").length === 2}
                >
                  {item.label}
                </Nav.Link>
              ))}
            </Nav>
            <div className="d-flex align-items-center gap-3 text-light">
              <span>
                {user.name} ({user.role})
              </span>
              <Button variant="outline-light" size="sm" onClick={handleLogout}>
                Log out
              </Button>
            </div>
          </>
        )}
      </Container>
    </Navbar>
  );
}
