import PageHeader from "../components/PageHeader.jsx";

// Shown for menu items whose feature card is not merged yet.
export default function ComingSoonPage({ title, card }) {
  return (
    <>
      <PageHeader title={title} />
      <div className="srs-panel srs-empty">
        <strong>This page is being built</strong>
        It arrives with card #{card}.
      </div>
    </>
  );
}
