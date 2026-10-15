import { useState } from "react";
import { Button, Offcanvas } from "react-bootstrap";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/authContext.js";
import Icon from "./Icon.jsx";
import { MENU_ITEMS_BY_ROLE, ROLE_LABELS } from "./menus.js";

// Shared frame for every logged-in page: sidebar menu for the role + page content.
// On small screens the sidebar becomes a slide-out panel opened from the top bar.
export default function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);
  const items = MENU_ITEMS_BY_ROLE[user.role] || [];

  async function handleLogout() {
    await logout();
    navigate("/login");
  }

  return (
    <div className="srs-shell">
      <Offcanvas
        show={menuOpen}
        onHide={() => setMenuOpen(false)}
        responsive="lg"
        className="srs-sidebar"
        aria-label="Main menu"
      >
        <Offcanvas.Body>
          <div className="srs-brand">
            <div className="srs-brand-name">Student Record System</div>
            <div className="srs-brand-role">{ROLE_LABELS[user.role]} workspace</div>
          </div>
          <nav className="srs-nav" aria-label="Role navigation">
            {items.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.path.split("/").length === 2}
                onClick={() => setMenuOpen(false)}
              >
                <Icon name={item.icon} />
                {item.label}
              </NavLink>
            ))}
          </nav>
          <div className="srs-user">
            <div className="srs-user-name">{user.name}</div>
            <div className="srs-user-email">{user.email}</div>
            <Button
              variant="outline-light"
              size="sm"
              className="btn-icon mt-3"
              onClick={handleLogout}
            >
              <Icon name="logout" size={16} />
              Log out
            </Button>
          </div>
        </Offcanvas.Body>
      </Offcanvas>

      <div className="srs-main">
        <div className="srs-topbar d-lg-none">
          <Button
            variant="outline-light"
            size="sm"
            onClick={() => setMenuOpen(true)}
            aria-label="Open menu"
          >
            <Icon name="menu" />
          </Button>
          <strong>Student Record System</strong>
        </div>
        <main className="srs-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
