import { useCallback, useEffect, useMemo, useState } from "react";
import { Alert, Button, ButtonGroup, Form, Spinner, Table } from "react-bootstrap";
import * as adminApi from "../../api/admin.js";
import EmptyState from "../../components/EmptyState.jsx";
import PageHeader from "../../components/PageHeader.jsx";
import { apiErrorMessage, useToast } from "../../components/toast.js";

const SEMESTERS = [1, 2, 3, 4, 5, 6, 7, 8];
const LABELS = { PAID: "Paid", UNPAID: "Unpaid", NONE: "Not set" };

function mostCommonSemester(students) {
  const tally = {};
  students.forEach((s) => {
    tally[s.semester] = (tally[s.semester] || 0) + 1;
  });
  const best = Object.entries(tally).sort((a, b) => b[1] - a[1])[0];
  return best ? Number(best[0]) : 1;
}

function StatusBadge({ status }) {
  const key = status || "NONE";
  return <span className={`srs-status srs-status-${key.toLowerCase()}`}>{LABELS[key]}</span>;
}

export default function FeesPage() {
  const toast = useToast();
  const [semester, setSemester] = useState(null);
  const [students, setStudents] = useState(null);
  const [fees, setFees] = useState({});
  const [loadError, setLoadError] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [search, setSearch] = useState("");
  const [savingId, setSavingId] = useState(null);

  // Load students once, and open the semester most students are in.
  useEffect(() => {
    adminApi
      .listStudents()
      .then((list) => {
        setStudents(list);
        setSemester((current) => current ?? mostCommonSemester(list));
      })
      .catch((error) => setLoadError(apiErrorMessage(error)));
  }, []);

  const loadFees = useCallback(async () => {
    if (semester === null) return;
    try {
      const feeList = await adminApi.listFees(semester);
      setFees(Object.fromEntries(feeList.map((f) => [f.student_id, f.status])));
      setLoadError("");
    } catch (error) {
      setLoadError(apiErrorMessage(error));
    }
  }, [semester]);

  useEffect(() => {
    loadFees();
  }, [loadFees]);

  const counts = useMemo(() => {
    const result = { PAID: 0, UNPAID: 0, NONE: 0 };
    (students || []).forEach((s) => {
      result[fees[s.id] || "NONE"] += 1;
    });
    return result;
  }, [students, fees]);

  const visible = useMemo(() => {
    const term = search.trim().toLowerCase();
    return (students || []).filter(
      (s) =>
        (!statusFilter || (fees[s.id] || "NONE") === statusFilter) &&
        (!term || s.name.toLowerCase().includes(term) || s.srn.toLowerCase().includes(term)),
    );
  }, [students, fees, statusFilter, search]);

  async function mark(student, status) {
    setSavingId(student.id);
    try {
      await adminApi.setFee(student.id, semester, status);
      setFees((current) => ({ ...current, [student.id]: status }));
      toast(`${student.name}: semester ${semester} fees marked ${LABELS[status].toLowerCase()}`);
    } catch (error) {
      toast(apiErrorMessage(error), "danger");
    } finally {
      setSavingId(null);
    }
  }

  return (
    <>
      <PageHeader
        title="Fee Status"
        description="Students with unpaid fees cannot register for the ESA of that semester."
        action={
          <Form.Select
            value={semester ?? ""}
            onChange={(e) => setSemester(Number(e.target.value))}
            aria-label="Semester"
            style={{ width: "auto" }}
          >
            {SEMESTERS.map((s) => (
              <option key={s} value={s}>
                Semester {s}
              </option>
            ))}
          </Form.Select>
        }
      />

      {loadError && <Alert variant="danger">{loadError}</Alert>}

      <section className="srs-panel">
        <div className="srs-toolbar">
          <Form.Control
            type="search"
            placeholder="Search by name or SRN"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            aria-label="Search students"
          />
          <ButtonGroup aria-label="Filter by status">
            {[
              ["", `All ${students ? students.length : ""}`.trim()],
              ["PAID", `Paid ${counts.PAID}`],
              ["UNPAID", `Unpaid ${counts.UNPAID}`],
              ["NONE", `Not set ${counts.NONE}`],
            ].map(([value, label]) => (
              <Button
                key={value || "all"}
                variant={statusFilter === value ? "primary" : "outline-secondary"}
                onClick={() => setStatusFilter(value)}
                aria-pressed={statusFilter === value}
              >
                {label}
              </Button>
            ))}
          </ButtonGroup>
        </div>

        {!students && !loadError && (
          <div className="text-center py-5">
            <Spinner animation="border" role="status" aria-label="Loading fee status" />
          </div>
        )}
        {students && students.length === 0 && (
          <EmptyState title="No students yet">
            Add students first, then record their fees here.
          </EmptyState>
        )}
        {students && students.length > 0 && visible.length === 0 && (
          <EmptyState title="Nobody matches this filter">
            Choose another status or search term.
          </EmptyState>
        )}
        {visible.length > 0 && (
          <div className="table-responsive">
            <Table hover className="srs-table">
              <thead>
                <tr>
                  <th>SRN</th>
                  <th>Name</th>
                  <th>Section</th>
                  <th>Semester {semester}</th>
                  <th className="text-end">Mark as</th>
                </tr>
              </thead>
              <tbody>
                {visible.map((s) => {
                  const status = fees[s.id];
                  return (
                    <tr key={s.id}>
                      <td className="srs-srn">{s.srn}</td>
                      <td>{s.name}</td>
                      <td>
                        {s.department_name} {s.section_name}
                      </td>
                      <td>
                        <StatusBadge status={status} />
                      </td>
                      <td className="text-end text-nowrap">
                        <Button
                          size="sm"
                          variant={status === "PAID" ? "success" : "outline-success"}
                          className="me-2"
                          disabled={savingId === s.id || status === "PAID"}
                          onClick={() => mark(s, "PAID")}
                          aria-label={`Mark ${s.name} paid`}
                        >
                          Paid
                        </Button>
                        <Button
                          size="sm"
                          variant={status === "UNPAID" ? "danger" : "outline-danger"}
                          disabled={savingId === s.id || status === "UNPAID"}
                          onClick={() => mark(s, "UNPAID")}
                          aria-label={`Mark ${s.name} unpaid`}
                        >
                          Unpaid
                        </Button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </Table>
          </div>
        )}
      </section>
    </>
  );
}
