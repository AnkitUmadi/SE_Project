import { Card, Container } from "react-bootstrap";
import { useAuth } from "../auth/authContext.js";

const TITLES = {
  admin: "Admin dashboard",
  faculty: "Faculty dashboard",
  student: "Student dashboard",
};

// Placeholder home page for each role. Real dashboards come in later cards (#24).
export default function HomePage() {
  const { user } = useAuth();
  return (
    <Container>
      <h1 className="h3 mb-3">{TITLES[user.role]}</h1>
      <Card body>Welcome, {user.name}. Features for your role will appear here.</Card>
    </Container>
  );
}
