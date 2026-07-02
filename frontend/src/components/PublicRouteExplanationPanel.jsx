const explanationItems = [
  {
    label: "Route score",
    title: "Higher score means better fit",
    detail: "The score helps compare route options using preview signals such as route quality, transfer context and recommendation ranking.",
  },
  {
    label: "Transfer safety",
    title: "Check connection risk",
    detail: "One-transfer journeys should be checked for practical transfer time and station-change risk before real travel planning.",
  },
  {
    label: "Preview warning",
    title: "Not live booking data",
    detail: "RailYatra does not currently confirm live seats, fare, PNR, payment or ticket booking.",
  },
  {
    label: "Best demo use",
    title: "Compare, then explain why",
    detail: "Use DSNR to TPKR first, then show how RailYatra compares route choices and explains recommendation signals.",
  },
];

export default function PublicRouteExplanationPanel() {
  return (
    <section className="public-route-explanation" aria-label="How to read RailYatra route recommendations">
      <div className="public-route-explanation__intro">
        <span>Phase 9 route explanation</span>
        <strong>How to read the recommendation results</strong>
        <p>
          This section makes the demo easier to understand for users, investors and testers before route cards are redesigned further.
        </p>
      </div>

      <div className="public-route-explanation__grid">
        {explanationItems.map((item) => (
          <article key={item.label}>
            <span>{item.label}</span>
            <strong>{item.title}</strong>
            <p>{item.detail}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
