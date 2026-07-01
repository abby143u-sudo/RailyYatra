export default function PublicDemoWarningBanner() {
  return (
    <section className="public-demo-warning-banner" aria-label="RailYatra public demo warning">
      <div className="public-demo-warning-banner__content">
        <div>
          <p className="public-demo-warning-banner__eyebrow">Public beta preview</p>
          <h2>RailYatra is a real railway route recommendation preview.</h2>
        </div>

        <div className="public-demo-warning-banner__status">
          <span>Live booking</span>
          <strong>Not connected</strong>
        </div>
      </div>

      <p className="public-demo-warning-banner__message">
        Live ticket booking, PNR, payment, cancellation, live fare and live seat availability are not connected yet.
        Use this demo for route discovery, ranked recommendations, transfer safety and product preview only.
      </p>
    </section>
  );
}
