import { useEffect, useState } from "react";
import { Alert, Container } from "react-bootstrap";
import { getHealth } from "./api/client.js";

export default function App() {
  const [status, setStatus] = useState("checking");

  useEffect(() => {
    getHealth()
      .then((data) => setStatus(data.status === "ok" ? "online" : "offline"))
      .catch(() => setStatus("offline"));
  }, []);

  return (
    <Container className="py-5">
      <h1 className="mb-4">Student Record System</h1>
      {status === "checking" && <Alert variant="secondary">Checking backend…</Alert>}
      {status === "online" && <Alert variant="success">Backend is online ✅</Alert>}
      {status === "offline" && (
        <Alert variant="danger">Backend is offline. Start it with: python run.py</Alert>
      )}
    </Container>
  );
}
