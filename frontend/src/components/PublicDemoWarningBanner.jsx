export default function PublicDemoWarningBanner() {
  return (
    <section
      className="public-demo-warning-banner"
      aria-label="RailBay public beta notice"
    >
      <div className="public-demo-warning-banner__content">
        <div>
          <p className="public-demo-warning-banner__eyebrow">
            Public Beta · v0.9.0-beta
          </p>

          <h2>
            RailBay route recommendations are live in public beta.
          </h2>
        </div>

        <div className="public-demo-warning-banner__status">
          <span>Launch status</span>
          <strong>Route beta live</strong>
        </div>
      </div>

      <p className="public-demo-warning-banner__message">
        Explore real-data routes, ranked journeys, estimated dates,
        duration and transfer safety. Live fares, seat availability,
        PNR, booking, payments and cancellation are not connected.
      </p>
    </section>
  );
}
