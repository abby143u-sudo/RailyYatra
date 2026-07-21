export default function PublicDemoHero() {
  return (
    <section className="public-demo-hero">
      <div className="public-demo-hero__content">
        <p className="public-demo-hero__eyebrow">
          RailBay public beta
        </p>

        <h1>
          Find smarter train routes, not just direct trains
        </h1>

        <p className="public-demo-hero__subtitle">
          Compare direct, one-transfer and alternative railway
          journeys with clear route scoring, travel context and
          safety warnings.
        </p>

        <div className="public-demo-hero__actions">
          <a href="#main-search">Search train routes</a>
          <a href="#about">How RailBay works</a>
        </div>
      </div>

      <div
        className="public-demo-hero__card"
        aria-label="RailBay journey-planning features"
      >
        <span>RailBay compares</span>
        <strong>More than the obvious route</strong>

        <ul className="public-demo-hero__highlights">
          <li>Direct train options</li>
          <li>One-transfer alternatives</li>
          <li>Journey scoring and route context</li>
          <li>Cloud-saved journeys</li>
        </ul>
      </div>

      <div className="public-demo-hero__safety">
        <strong>Public beta:</strong> Ticket booking, payment,
        PNR, confirmed live fares and live seat availability
        are not connected yet.
      </div>
    </section>
  );
}
