import { Navigate } from "react-router-dom";
import { HOME_BY_ROLE, useAuth } from "../auth/authContext.js";

// Guards a page: not logged in -> login page; wrong role -> your own home page.
// (This only hides pages in the browser. The real security check is on the server, card #5.)
export default function RequireRole({ role, children }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  if (user.role !== role) return <Navigate to={HOME_BY_ROLE[user.role]} replace />;
  return children;
}
