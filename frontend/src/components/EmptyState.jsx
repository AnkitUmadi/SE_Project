export default function EmptyState({ title, children }) {
  return (
    <div className="srs-empty">
      <strong>{title}</strong>
      {children}
    </div>
  );
}
