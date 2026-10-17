import { useCallback, useState } from "react";
import { Toast, ToastContainer } from "react-bootstrap";
import { ToastContext } from "./toast.js";

export default function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const show = useCallback((message, variant = "success") => {
    const id = Date.now() + Math.random();
    setToasts((list) => [...list, { id, message, variant }]);
  }, []);

  const remove = (id) => setToasts((list) => list.filter((t) => t.id !== id));

  return (
    <ToastContext.Provider value={show}>
      {children}
      <ToastContainer position="bottom-end" className="p-3" style={{ zIndex: 2000 }}>
        {toasts.map((t) => (
          <Toast
            key={t.id}
            onClose={() => remove(t.id)}
            delay={3500}
            autohide
            bg={t.variant === "danger" ? "danger" : "dark"}
          >
            <Toast.Body className="text-white" role="status">
              {t.message}
            </Toast.Body>
          </Toast>
        ))}
      </ToastContainer>
    </ToastContext.Provider>
  );
}
