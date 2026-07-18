export default function PublicDemoFooter() {
  return (
    <footer className="public-demo-footer" aria-label="RailBay public demo status">
      <div className="public-demo-footer__brand">
        <span>RailBay</span>
        <strong>Public demo preview is live</strong>
        <p>
          Real railway route recommendation preview with staging railway data, ranked recommendations and transfer-safety context.
        </p>
      </div>

      <div className="public-demo-footer__grid">
        <article>
          <span>Status</span>
          <strong>Preview mode</strong>
          <p>No live booking, payment, PNR, live fare or live seat availability yet.</p>
        </article>
        <article>
          <span>Demo route</span>
          <strong>DSNR → TPKR</strong>
          <p>Recommended route for showing direct and one-transfer intelligence.</p>
        </article>
        <article>
          <span>Phase</span>
          <strong>Phase 8</strong>
          <p>Public demo polish, mobile UX and investor/demo flow.</p>
        </article>
      </div>

      <div className="public-demo-footer__links">
        <a href="https://raily-yatra.vercel.app">Frontend demo</a>
        <a href="https://api.railbay.xyz">Backend API</a>
      </div>
    </footer>
  );
}
