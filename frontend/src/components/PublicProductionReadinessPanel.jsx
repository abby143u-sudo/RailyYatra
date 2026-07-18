const checklist = [
  {
    title: "Real railway data",
    status: "Ready",
    detail:
      "8,990 stations, 5,208 trains and 417,080 train stops are available.",
  },
  {
    title: "Date-aware route recommendations",
    status: "Ready",
    detail:
      "Direct and transfer journeys include estimated dates and duration.",
  },
  {
    title: "Transfer safety and deduplication",
    status: "Ready",
    detail:
      "Unsafe short transfers are rejected and equivalent routes are collapsed.",
  },
  {
    title: "Caching and resilient frontend",
    status: "Ready",
    detail:
      "Repeated searches are cached and users receive timeout, retry and loading feedback.",
  },
  {
    title: "Production smoke testing",
    status: "Ready",
    detail:
      "Live frontend, backend, data health, recommendations and cache are tested.",
  },
  {
    title: "Scheduled production monitoring",
    status: "Ready",
    detail:
      "GitHub Actions checks the public beta every six hours.",
  },
  {
    title: "Live fares and availability",
    status: "Planned",
    detail:
      "Official live fare and seat-availability integrations are not connected.",
  },
  {
    title: "Booking, PNR and payments",
    status: "Planned",
    detail:
      "Ticket booking and transaction features remain part of the commercial roadmap.",
  },
];

export default function PublicProductionReadinessPanel() {
  return (
    <section
      className="public-production-readiness"
      aria-label="RailBay public beta readiness"
    >
      <div className="public-production-readiness__intro">
        <span>Public Beta · v0.9.0-beta</span>
        <strong>GO for route-recommendation public beta</strong>

        <p>
          RailBay is ready for public testing as a railway route
          discovery and recommendation product. It must not be
          presented as a live ticket-booking platform.
        </p>
      </div>

      <div className="public-production-readiness__grid">
        {checklist.map((item) => (
          <article
            key={item.title}
            className={
              "public-production-readiness__item " +
              `public-production-readiness__item--${item.status.toLowerCase()}`
            }
          >
            <div>
              <span>{item.status}</span>
              <strong>{item.title}</strong>
            </div>

            <p>{item.detail}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
