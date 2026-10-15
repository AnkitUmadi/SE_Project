import { useEffect, useMemo, useState } from "react";
import { Alert, Button, Container, Form, Modal, Spinner, Table } from "react-bootstrap";
import * as coursesApi from "../../api/courses.js";
import { apiErrorMessage } from "../../api/errors.js";
import EnrollmentPanel from "../../components/EnrollmentPanel.jsx";

const EMPTY_FORM = {
  code: "",
  name: "",
  credits: 4,
  department_id: "",
  faculty_id: "",
  syllabus: "",
};

// Form values (strings from inputs) -> the JSON the API expects.
function toPayload(form) {
  return {
    code: form.code,
    name: form.name,
    credits: Number(form.credits),
    department_id: form.department_id === "" ? null : Number(form.department_id),
    faculty_id: form.faculty_id === "" ? null : Number(form.faculty_id),
    syllabus: form.syllabus,
  };
}

// Admin Courses page: list, search, add / edit / delete courses, view syllabus,
// and manage each course's enrolled students (issues #11, #12).
export default function CoursesPage() {
  const [courses, setCourses] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [faculty, setFaculty] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");

  const [editing, setEditing] = useState(null); // null = closed, {} = new, course = edit
  const [form, setForm] = useState(EMPTY_FORM);
  const [formError, setFormError] = useState("");
  const [saving, setSaving] = useState(false);

  const [deleting, setDeleting] = useState(null);
  const [syllabusCourse, setSyllabusCourse] = useState(null);
  const [rosterCourse, setRosterCourse] = useState(null);

  useEffect(() => {
    Promise.all([
      coursesApi.listCourses().then(setCourses),
      coursesApi.listDepartments().then(setDepartments),
      coursesApi.listFaculty().then(setFaculty),
    ])
      .catch((err) => setError(apiErrorMessage(err)))
      .finally(() => setLoading(false));
  }, []);

  const visibleCourses = useMemo(() => {
    const term = search.trim().toLowerCase();
    if (!term) return courses;
    return courses.filter(
      (course) =>
        course.code.toLowerCase().includes(term) || course.name.toLowerCase().includes(term),
    );
  }, [courses, search]);

  function openForm(course) {
    setFormError("");
    setEditing(course || {});
    setForm(
      course
        ? {
            code: course.code,
            name: course.name,
            credits: course.credits,
            department_id: String(course.department_id ?? ""),
            faculty_id: String(course.faculty_id ?? ""),
            syllabus: course.syllabus,
          }
        : { ...EMPTY_FORM, department_id: String(departments[0]?.id ?? "") },
    );
  }

  function setField(name) {
    return (event) => setForm({ ...form, [name]: event.target.value });
  }

  async function handleSave(event) {
    event.preventDefault();
    setFormError("");
    setSaving(true);
    try {
      if (editing.id) {
        const updated = await coursesApi.updateCourse(editing.id, toPayload(form));
        setCourses(courses.map((course) => (course.id === updated.id ? updated : course)));
        if (rosterCourse?.id === updated.id) setRosterCourse(updated);
      } else {
        const created = await coursesApi.createCourse(toPayload(form));
        setCourses([...courses, created].sort((a, b) => a.code.localeCompare(b.code)));
      }
      setEditing(null);
    } catch (err) {
      setFormError(apiErrorMessage(err, "Could not save the course."));
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    setError("");
    try {
      await coursesApi.deleteCourse(deleting.id);
      setCourses(courses.filter((course) => course.id !== deleting.id));
      if (rosterCourse?.id === deleting.id) setRosterCourse(null);
    } catch (err) {
      setError(apiErrorMessage(err, "Could not delete the course."));
    } finally {
      setDeleting(null);
    }
  }

  return (
    <Container className="pb-5">
      <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-3">
        <h1 className="h3 mb-0">Courses &amp; Enrollment</h1>
        <Button onClick={() => openForm(null)}>Add course</Button>
      </div>

      {error && <Alert variant="danger">{error}</Alert>}

      <Form.Control
        className="mb-3"
        type="search"
        placeholder="Search by course code or name"
        aria-label="Search courses"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />

      {loading ? (
        <Spinner animation="border" role="status" aria-label="Loading courses" />
      ) : visibleCourses.length === 0 ? (
        <p className="text-muted">
          {courses.length === 0 ? "No courses yet. Add the first one." : "No matching courses."}
        </p>
      ) : (
        <Table striped hover responsive>
          <thead>
            <tr>
              <th>Code</th>
              <th>Name</th>
              <th>Credits</th>
              <th>Department</th>
              <th>Faculty</th>
              <th aria-label="Actions" />
            </tr>
          </thead>
          <tbody>
            {visibleCourses.map((course) => (
              <tr key={course.id} className={rosterCourse?.id === course.id ? "table-active" : ""}>
                <td>
                  <Button
                    variant="link"
                    className="p-0"
                    onClick={() => setSyllabusCourse(course)}
                    title="Show syllabus"
                  >
                    {course.code}
                  </Button>
                </td>
                <td>{course.name}</td>
                <td>{course.credits}</td>
                <td>{course.department_name}</td>
                <td>{course.faculty_name || <span className="text-muted">Not assigned</span>}</td>
                <td className="text-end text-nowrap">
                  <Button
                    size="sm"
                    variant="outline-primary"
                    className="me-2"
                    onClick={() => setRosterCourse(course)}
                    aria-label={`Students in ${course.code}`}
                  >
                    Students
                  </Button>
                  <Button
                    size="sm"
                    variant="outline-secondary"
                    className="me-2"
                    onClick={() => openForm(course)}
                    aria-label={`Edit ${course.code}`}
                  >
                    Edit
                  </Button>
                  <Button
                    size="sm"
                    variant="outline-danger"
                    onClick={() => setDeleting(course)}
                    aria-label={`Delete ${course.code}`}
                  >
                    Delete
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      )}

      {rosterCourse && <EnrollmentPanel course={rosterCourse} />}

      <Modal show={editing !== null} onHide={() => setEditing(null)} size="lg">
        <Form onSubmit={handleSave}>
          <Modal.Header closeButton>
            <Modal.Title>{editing?.id ? `Edit ${editing.code}` : "Add course"}</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            {formError && <Alert variant="danger">{formError}</Alert>}
            <Form.Group className="mb-3" controlId="course-code">
              <Form.Label>Course code</Form.Label>
              <Form.Control value={form.code} onChange={setField("code")} required />
            </Form.Group>
            <Form.Group className="mb-3" controlId="course-name">
              <Form.Label>Course name</Form.Label>
              <Form.Control value={form.name} onChange={setField("name")} required />
            </Form.Group>
            <Form.Group className="mb-3" controlId="course-credits">
              <Form.Label>Credits</Form.Label>
              <Form.Control
                type="number"
                min={1}
                max={6}
                value={form.credits}
                onChange={setField("credits")}
                required
              />
            </Form.Group>
            <Form.Group className="mb-3" controlId="course-department">
              <Form.Label>Department</Form.Label>
              <Form.Select value={form.department_id} onChange={setField("department_id")} required>
                <option value="">Choose a department</option>
                {departments.map((department) => (
                  <option key={department.id} value={department.id}>
                    {department.name}
                  </option>
                ))}
              </Form.Select>
            </Form.Group>
            <Form.Group className="mb-3" controlId="course-faculty">
              <Form.Label>Faculty</Form.Label>
              <Form.Select value={form.faculty_id} onChange={setField("faculty_id")}>
                <option value="">Not assigned</option>
                {faculty.map((member) => (
                  <option key={member.id} value={member.id}>
                    {member.name}
                  </option>
                ))}
              </Form.Select>
            </Form.Group>
            <Form.Group controlId="course-syllabus">
              <Form.Label>Syllabus</Form.Label>
              <Form.Control
                as="textarea"
                rows={5}
                value={form.syllabus}
                onChange={setField("syllabus")}
              />
            </Form.Group>
          </Modal.Body>
          <Modal.Footer>
            <Button variant="secondary" onClick={() => setEditing(null)}>
              Cancel
            </Button>
            <Button type="submit" disabled={saving}>
              {saving ? "Saving…" : "Save"}
            </Button>
          </Modal.Footer>
        </Form>
      </Modal>

      <Modal show={deleting !== null} onHide={() => setDeleting(null)}>
        <Modal.Header closeButton>
          <Modal.Title>Delete course?</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          Delete <strong>{deleting?.code}</strong> – {deleting?.name}? Its enrollments and
          attendance will also be deleted.
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setDeleting(null)}>
            Cancel
          </Button>
          <Button variant="danger" onClick={handleDelete}>
            Delete
          </Button>
        </Modal.Footer>
      </Modal>

      <Modal show={syllabusCourse !== null} onHide={() => setSyllabusCourse(null)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>
            {syllabusCourse?.code} – {syllabusCourse?.name}
          </Modal.Title>
        </Modal.Header>
        <Modal.Body style={{ whiteSpace: "pre-wrap" }}>
          {syllabusCourse?.syllabus || <span className="text-muted">No syllabus entered yet.</span>}
        </Modal.Body>
      </Modal>
    </Container>
  );
}
