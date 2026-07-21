export default function PublicDemoFooter() {
  const currentYear = new Date().getFullYear();

  return (
    <footer
      className="public-demo-footer"
      aria-label="RailBay footer"
    >
      <div className="public-demo-footer__brand">
        <span>RailBay</span>
        <strong>Smarter railway route recommendations</strong>
        <p>
          Compare direct and alternative railway journeys
          before checking final details with an authorised
          railway source.
        </p>
      </div>

      <nav
        className="public-demo-footer__links"
        aria-label="Footer navigation"
      >
        <a href="#main-search">Route search</a>
        <a href="#about">About</a>
        <a href="#privacy">Privacy</a>
        <a href="#terms">Terms</a>
        <a href="#contact">Contact</a>
      </nav>

      <div className="public-demo-footer__legal">
        <span>© {currentYear} RailBay</span>
        <span>Independent public-beta railway planner</span>
      </div>
    </footer>
  );
}
