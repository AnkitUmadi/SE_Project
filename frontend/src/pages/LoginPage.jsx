import { useState } from "react";
import { Alert, Button, Card, Container, Form } from "react-bootstrap";
import { Navigate, useNavigate } from "react-router-dom";
import { HOME_BY_ROLE, useAuth } from "../auth/authContext.js";

// Turn an API error into a sentence the user understands.
function errorMessage(error) {
  if (!error.response) return "Cannot reach the server. Is the backend running (python run.py)?";
  return error.response.data?.error || "Login failed. Please try again.";
}

export default function LoginPage() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (user) return <Navigate to={HOME_BY_ROLE[user.role]} replace />;

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const loggedIn = await login(email, password);
      navigate(HOME_BY_ROLE[loggedIn.role]);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Container className="d-flex justify-content-center">
      <Card style={{ maxWidth: 420, width: "100%" }}>
        <Card.Body>
          <Card.Title as="h1" className="h4 mb-3">
            Log in
          </Card.Title>
          {error && <Alert variant="danger">{error}</Alert>}
          <Form onSubmit={handleSubmit}>
            <Form.Group className="mb-3" controlId="email">
              <Form.Label>Email</Form.Label>
              <Form.Control
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="username"
              />
            </Form.Group>
            <Form.Group className="mb-3" controlId="password">
              <Form.Label>Password</Form.Label>
              <Form.Control
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
              />
            </Form.Group>
            <Button type="submit" className="w-100" disabled={submitting}>
              {submitting ? "Logging in…" : "Log in"}
            </Button>
          </Form>
        </Card.Body>
      </Card>
    </Container>
  );
}
