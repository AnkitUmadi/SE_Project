import { useCallback, useEffect, useState } from "react";
import { Alert, Button, Form, InputGroup, Modal, Spinner } from "react-bootstrap";
import * as adminApi from "../../api/admin.js";
import ConfirmDialog from "../../components/ConfirmDialog.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import Icon from "../../components/Icon.jsx";
import PageHeader from "../../components/PageHeader.jsx";
import { apiErrorMessage, useToast } from "../../components/toast.js";

// One department card: its sections as chips, plus an inline "add section" box.
function DepartmentCard({ department, onAddSection, onRemoveSection, onDelete }) {
  const [sectionName, setSectionName] = useState("");
  const [saving, setSaving] = useState(false);

  async function handleAdd(event) {
    event.preventDefault();
    if (!sectionName.trim()) return;
    setSaving(true);
    const ok = await onAddSection(department, sectionName.trim());
    setSaving(false);
    if (ok) setSectionName("");
  }

  const count = department.sections.length;
  return (
    <article className="srs-dept" aria-label={department.name}>
      <div className="srs-dept-head">
        <div>
          <h2 className="srs-dept-name">{department.name}</h2>
          <div className="srs-dept-count">{count === 1 ? "1 section" : `${count} sections`}</div>
        </div>
        <Button
          variant="outline-danger"
          size="sm"
          onClick={() => onDelete(department)}
          aria-label={`Delete ${department.name}`}
        >
          <Icon name="trash" size={16} />
        </Button>
      </div>

      {count > 0 ? (
        <div className="srs-sections">
          {department.sections.map((section) => (
            <span key={section.id} className="srs-section-chip">
              {section.name}
              <button
                type="button"
                className="srs-chip-remove"
                onClick={() => onRemoveSection(section, department)}
                aria-label={`Remove section ${section.name}`}
              >
                <Icon name="close" size={14} />
              </button>
            </span>
          ))}
        </div>
      ) : (
        <div className="text-body-secondary small">No sections yet.</div>
      )}

      <Form onSubmit={handleAdd}>
        <InputGroup size="sm">
          <Form.Control
            placeholder="New section, e.g. A"
            value={sectionName}
            onChange={(e) => setSectionName(e.target.value)}
            aria-label={`New section name for ${department.name}`}
          />
          <Button type="submit" variant="outline-primary" disabled={saving}>
            Add section
          </Button>
        </InputGroup>
      </Form>
    </article>
  );
}

export default function DepartmentsPage() {
  const toast = useToast();
  const [departments, setDepartments] = useState(null);
  const [loadError, setLoadError] = useState("");
  const [showAdd, setShowAdd] = useState(false);
  const [newName, setNewName] = useState("");
  const [formError, setFormError] = useState("");
  const [confirm, setConfirm] = useState(null);

  const load = useCallback(async () => {
    try {
      setDepartments(await adminApi.listDepartments());
      setLoadError("");
    } catch (error) {
      setLoadError(apiErrorMessage(error));
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function handleCreate(event) {
    event.preventDefault();
    setFormError("");
    try {
      await adminApi.createDepartment(newName.trim());
      toast(`Department ${newName.trim()} added`);
      setShowAdd(false);
      setNewName("");
      load();
    } catch (error) {
      setFormError(apiErrorMessage(error));
    }
  }

  async function handleAddSection(department, name) {
    try {
      await adminApi.createSection(department.id, name);
      toast(`Section ${name} added to ${department.name}`);
      load();
      return true;
    } catch (error) {
      toast(apiErrorMessage(error), "danger");
      return false;
    }
  }

  async function runConfirmed() {
    const { kind, item, department } = confirm;
    setConfirm(null);
    try {
      if (kind === "department") {
        await adminApi.deleteDepartment(item.id);
        toast(`Department ${item.name} deleted`);
      } else {
        await adminApi.deleteSection(item.id);
        toast(`Section ${item.name} removed from ${department.name}`);
      }
      load();
    } catch (error) {
      toast(apiErrorMessage(error), "danger");
    }
  }

  return (
    <>
      <PageHeader
        title="Departments & Sections"
        description="Every student belongs to one section, and every section to one department."
        action={
          <Button className="btn-srs btn-icon" onClick={() => setShowAdd(true)}>
            <Icon name="plus" />
            Add department
          </Button>
        }
      />

      {loadError && <Alert variant="danger">{loadError}</Alert>}
      {!departments && !loadError && (
        <div className="text-center py-5">
          <Spinner animation="border" role="status" aria-label="Loading departments" />
        </div>
      )}
      {departments && departments.length === 0 && (
        <div className="srs-panel">
          <EmptyState title="No departments yet">
            Add the first department, then add its sections.
          </EmptyState>
        </div>
      )}
      {departments && departments.length > 0 && (
        <div className="srs-dept-grid">
          {departments.map((department) => (
            <DepartmentCard
              key={department.id}
              department={department}
              onAddSection={handleAddSection}
              onRemoveSection={(section, dept) =>
                setConfirm({ kind: "section", item: section, department: dept })
              }
              onDelete={(dept) => setConfirm({ kind: "department", item: dept })}
            />
          ))}
        </div>
      )}

      <Modal show={showAdd} onHide={() => setShowAdd(false)} centered>
        <Form onSubmit={handleCreate}>
          <Modal.Header closeButton>
            <Modal.Title as="h2" className="h5">
              Add department
            </Modal.Title>
          </Modal.Header>
          <Modal.Body>
            {formError && <Alert variant="danger">{formError}</Alert>}
            <Form.Group controlId="department-name">
              <Form.Label>Department name</Form.Label>
              <Form.Control
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="e.g. CSE (AI & ML)"
                required
                autoFocus
              />
            </Form.Group>
          </Modal.Body>
          <Modal.Footer>
            <Button variant="outline-secondary" onClick={() => setShowAdd(false)}>
              Cancel
            </Button>
            <Button type="submit" className="btn-srs">
              Add department
            </Button>
          </Modal.Footer>
        </Form>
      </Modal>

      <ConfirmDialog
        show={Boolean(confirm)}
        title={confirm?.kind === "department" ? "Delete department?" : "Remove section?"}
        body={
          confirm?.kind === "department"
            ? `${confirm.item.name} and all its sections will be deleted.`
            : confirm &&
              `Section ${confirm.item.name} will be removed from ${confirm.department.name}.`
        }
        confirmLabel={confirm?.kind === "department" ? "Delete department" : "Remove section"}
        onConfirm={runConfirmed}
        onCancel={() => setConfirm(null)}
      />
    </>
  );
}
