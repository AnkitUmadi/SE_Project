// Title, one-line description and (optionally) the page's main action button.
export default function PageHeader({ title, description, action }) {
  return (
    <header className="srs-page-header">
      <div>
        <h1>{title}</h1>
        {description && <p>{description}</p>}
      </div>
      {action}
    </header>
  );
}
