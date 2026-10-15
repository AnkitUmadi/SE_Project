import { useEffect, useState } from "react";
import { Accordion, Alert, Button, Container, Form, Spinner } from "react-bootstrap";
import * as coursesApi from "../api/courses.js";
import { apiErrorMessage } from "../api/errors.js";
import { useAuth } from "../auth/authContext.js";

// "My Courses" for Faculty (courses they teach) and Students (courses they are enrolled in).
// Clicking a course shows its syllabus; Faculty can edit it (SRS-F-009, issue #11).
export default function MyCoursesPage() {
  const { user } = useAuth();
  const canEdit = user.role === "faculty";
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [editingId, setEditingId] = useState(null);
  const [draft, setDraft] = useState("");

  useEffect(() => {
    coursesApi
      .listMyCourses(user.role)
      .then(setCourses)
      .catch((err) => setError(apiErrorMessage(err)))
      .finally(() => setLoading(false));
  }, [user.role]);

  function startEditing(course) {
    setError("");
    setEditingId(course.id);
    setDraft(course.syllabus);
  }

  async function saveSyllabus(courseId) {
    setError("");
    try {
      const updated = await coursesApi.updateSyllabus(courseId, draft);
      setCourses(courses.map((course) => (course.id === updated.id ? updated : course)));
      setEditingId(null);
    } catch (err) {
      setError(apiErrorMessage(err, "Could not save the syllabus."));
    }
  }

  return (
    <Container className="pb-5">
      <h1 className="h3 mb-3">My Courses</h1>
      {error && <Alert variant="danger">{error}</Alert>}
      {loading ? (
        <Spinner animation="border" role="status" aria-label="Loading courses" />
      ) : courses.length === 0 ? (
        <p className="text-muted">
          {canEdit
            ? "You are not assigned to any courses yet."
            : "You are not enrolled in any courses yet."}
        </p>
      ) : (
        <Accordion>
          {courses.map((course) => (
            <Accordion.Item key={course.id} eventKey={String(course.id)}>
              <Accordion.Header>
                {course.code} – {course.name} ({course.credits} credits)
              </Accordion.Header>
              <Accordion.Body>
                {!canEdit && course.faculty_name && (
                  <p className="text-muted mb-2">Faculty: {course.faculty_name}</p>
                )}
                {editingId === course.id ? (
                  <>
                    <Form.Control
                      as="textarea"
                      rows={6}
                      aria-label={`Syllabus for ${course.code}`}
                      value={draft}
                      onChange={(e) => setDraft(e.target.value)}
                    />
                    <div className="mt-2 d-flex gap-2">
                      <Button size="sm" onClick={() => saveSyllabus(course.id)}>
                        Save syllabus
                      </Button>
                      <Button size="sm" variant="secondary" onClick={() => setEditingId(null)}>
                        Cancel
                      </Button>
                    </div>
                  </>
                ) : (
                  <>
                    <div style={{ whiteSpace: "pre-wrap" }}>
                      {course.syllabus || (
                        <span className="text-muted">No syllabus entered yet.</span>
                      )}
                    </div>
                    {canEdit && (
                      <Button
                        size="sm"
                        variant="outline-primary"
                        className="mt-2"
                        onClick={() => startEditing(course)}
                      >
                        Edit syllabus
                      </Button>
                    )}
                  </>
                )}
              </Accordion.Body>
            </Accordion.Item>
          ))}
        </Accordion>
      )}
    </Container>
  );
}
