import { useCallback, useEffect, useMemo, useState } from "react";
import { Alert, Button, Card, Col, Form, Row, Spinner, Table } from "react-bootstrap";
import * as coursesApi from "../api/courses.js";
import { apiErrorMessage } from "../api/errors.js";

// Course roster for the Admin: see enrolled students, add more, or remove them (issue #12).
export default function EnrollmentPanel({ course }) {
  const [roster, setRoster] = useState([]);
  const [allStudents, setAllStudents] = useState([]);
  const [selected, setSelected] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const loadRoster = useCallback(async () => {
    setRoster(await coursesApi.listEnrolledStudents(course.id));
  }, [course.id]);

  useEffect(() => {
    setLoading(true);
    setError("");
    setMessage("");
    setSelected([]);
    Promise.all([loadRoster(), coursesApi.listStudents().then(setAllStudents)])
      .catch((err) => setError(apiErrorMessage(err)))
      .finally(() => setLoading(false));
  }, [loadRoster]);

  // Only offer students who are not enrolled yet.
  const available = useMemo(() => {
    const enrolledIds = new Set(roster.map((student) => student.id));
    return allStudents.filter((student) => !enrolledIds.has(student.id));
  }, [roster, allStudents]);

  async function handleEnroll(event) {
    event.preventDefault();
    setError("");
    setMessage("");
    try {
      const enrolled = await coursesApi.enrollStudents(course.id, selected.map(Number));
      setSelected([]);
      setMessage(`Enrolled ${enrolled.length} student(s).`);
      await loadRoster();
    } catch (err) {
      setError(apiErrorMessage(err, "Could not enroll the selected students."));
    }
  }

  async function handleRemove(student) {
    setError("");
    setMessage("");
    try {
      await coursesApi.removeEnrollment(course.id, student.id);
      setMessage(`Removed ${student.srn} from ${course.code}.`);
      await loadRoster();
    } catch (err) {
      setError(apiErrorMessage(err));
    }
  }

  return (
    <Card className="mt-4">
      <Card.Header as="h2" className="h5">
        Students enrolled in {course.code} – {course.name}
      </Card.Header>
      <Card.Body>
        {error && <Alert variant="danger">{error}</Alert>}
        {message && <Alert variant="success">{message}</Alert>}
        {loading ? (
          <Spinner animation="border" size="sm" role="status" aria-label="Loading roster" />
        ) : (
          <Row className="g-4">
            <Col md={7}>
              {roster.length === 0 ? (
                <p className="text-muted">No students enrolled yet.</p>
              ) : (
                <Table size="sm" striped hover responsive>
                  <thead>
                    <tr>
                      <th>SRN</th>
                      <th>Name</th>
                      <th>Section</th>
                      <th aria-label="Actions" />
                    </tr>
                  </thead>
                  <tbody>
                    {roster.map((student) => (
                      <tr key={student.id}>
                        <td>{student.srn}</td>
                        <td>{student.name}</td>
                        <td>{student.section_name}</td>
                        <td className="text-end">
                          <Button
                            size="sm"
                            variant="outline-danger"
                            onClick={() => handleRemove(student)}
                            aria-label={`Remove ${student.srn}`}
                          >
                            Remove
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              )}
            </Col>
            <Col md={5}>
              <Form onSubmit={handleEnroll}>
                <Form.Group controlId="enroll-students" className="mb-2">
                  <Form.Label>Add students</Form.Label>
                  <Form.Select
                    multiple
                    htmlSize={8}
                    value={selected}
                    onChange={(e) =>
                      setSelected(Array.from(e.target.selectedOptions, (option) => option.value))
                    }
                  >
                    {available.map((student) => (
                      <option key={student.id} value={student.id}>
                        {student.srn} – {student.name}
                      </option>
                    ))}
                  </Form.Select>
                  <Form.Text>Hold Ctrl (or Cmd) to pick several students.</Form.Text>
                </Form.Group>
                <Button type="submit" disabled={selected.length === 0}>
                  Enroll selected
                </Button>
              </Form>
            </Col>
          </Row>
        )}
      </Card.Body>
    </Card>
  );
}
