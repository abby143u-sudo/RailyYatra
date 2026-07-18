export default function PublicDemoHero() {
  return (
    <section className="public-demo-hero">
      <div className="public-demo-hero__content">
        <p className="public-demo-hero__eyebrow">RailBay Public Demo</p>
        <h1>Real railway route recommendation preview</h1>
        <p className="public-demo-hero__subtitle">
          Explore route options, ranked recommendations and transfer-safety signals using real staging railway data.
        </p>
        <div className="public-demo-hero__actions">
          <a href="#main-search">Try route search</a>
          <a href="#recommendations-preview">View recommendation engine</a>
        </div>
      </div>
      <div className="public-demo-hero__card" aria-label="Demo route example">
        <span>Recommended demo route</span>
        <strong>DSNR → TPKR</strong>
        <p>Shows direct and one-transfer options with confidence and transfer-safety labels.</p>
      </div>
      <div className="public-demo-hero__safety">
        <strong>Preview mode:</strong> Live booking, payment, PNR, live fare and live seat availability are not connected yet.
      </div>
    </section>
  );
}
