import { Link } from "react-router-dom";
import { useAuth } from "../auth/authContext.js";
import Icon from "../components/Icon.jsx";
import { MENU_ITEMS_BY_ROLE } from "../components/menus.js";
import PageHeader from "../components/PageHeader.jsx";

const TITLES = {
  admin: "Admin dashboard",
  faculty: "Faculty dashboard",
  student: "Student dashboard",
};

// Home page for each role: a greeting and shortcuts to the role's pages.
// Summary numbers come with the dashboard card (#24).
export default function HomePage() {
  const { user } = useAuth();
  const shortcuts = (MENU_ITEMS_BY_ROLE[user.role] || []).slice(1);
  return (
    <>
      <PageHeader title={TITLES[user.role]} description={`Welcome back, ${user.name}.`} />
      <div className="srs-shortcuts">
        {shortcuts.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className="srs-panel p-3 d-flex align-items-center gap-3 text-decoration-none text-reset"
          >
            <Icon name={item.icon} size={22} />
            <span className="fw-semibold">{item.label}</span>
          </Link>
        ))}
      </div>
    </>
  );
}
