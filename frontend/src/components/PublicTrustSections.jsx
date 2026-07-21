const SUPPORT_EMAIL =
  import.meta.env.VITE_RAILBAY_SUPPORT_EMAIL ||
  "abby143u@gmail.com";

export default function PublicTrustSections() {
  return (
    <section
      className="public-trust-sections"
      aria-label="RailBay information and policies"
    >
      <article id="about" className="public-trust-card">
        <span>About RailBay</span>
        <h2>Smarter railway journey discovery</h2>
        <p>
          RailBay compares direct, transfer and alternative
          railway routes and explains recommendation signals
          such as journey duration, transfers and route risk.
        </p>
        <p>
          RailBay is currently a public-beta route-planning
          product. It is not a ticket-booking platform yet.
        </p>
      </article>

      <article id="privacy" className="public-trust-card">
        <span>Privacy</span>
        <h2>How account information is used</h2>
        <p>
          Account details are used to provide authentication,
          password recovery, email verification and cloud-saved
          journeys.
        </p>
        <p>
          RailBay may process technical logs and security data
          to prevent abuse and maintain service reliability.
          Infrastructure and email-delivery providers may process
          data required to operate these services.
        </p>
      </article>

      <article id="terms" className="public-trust-card">
        <span>Terms of use</span>
        <h2>Route information is advisory</h2>
        <p>
          RailBay recommendations are provided for journey
          planning and comparison. Timings, fares, availability
          and operational details may change.
        </p>
        <p>
          Always verify final journey information through an
          authorised railway source before travelling or making
          a payment.
        </p>
      </article>

      <article id="contact" className="public-trust-card">
        <span>Contact</span>
        <h2>Questions, feedback or bug reports</h2>
        <p>
          Share route-quality issues, account problems and
          product suggestions with the RailBay beta team.
        </p>
        <a
          className="public-trust-card__email"
          href={`mailto:${SUPPORT_EMAIL}`}
        >
          {SUPPORT_EMAIL}
        </a>
      </article>

      <div className="public-trust-disclaimer">
        RailBay is an independent railway route-planning
        product and is not affiliated with or endorsed by
        Indian Railways or IRCTC.
      </div>
    </section>
  );
}
