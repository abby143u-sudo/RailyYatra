const checklist = [
  {
    title: "Route recommendation preview",
    status: "Ready",
    detail: "Public demo can show route options, ranked recommendations and transfer-safety context.",
  },
  {
    title: "Live booking integration",
    status: "Pending",
    detail: "No live ticket booking is connected yet.",
  },
  {
    title: "Payment integration",
    status: "Pending",
    detail: "No payment collection or ticket purchase flow is connected.",
  },
  {
    title: "PNR integration",
    status: "Pending",
    detail: "PNR status, cancellation and booked-ticket lifecycle are not connected.",
  },
  {
    title: "Live fare and seat availability",
    status: "Pending",
    detail: "Current demo uses preview/staging data, not live fare or live availability.",
  },
  {
    title: "Production analytics and feedback backend",
    status: "Planned",
    detail: "Current analytics and feedback are browser-local only.",
  },
];

export default function PublicProductionReadinessPanel() {
  return (
    <section className="public-production-readiness" aria-label="RailYatra production readiness checklist">
      <div className="public-production-readiness__intro">
        <span>Phase 9 readiness</span>
        <strong>Production hardening checklist</strong>
        <p>
          RailYatra is stable as a public route recommendation preview. These are the major items required before it can be positioned as a live booking product.
        </p>
      </div>

      <div className="public-production-readiness__grid">
        {checklist.map((item) => (
          <article
            key={item.title}
            className={`public-production-readiness__item public-production-readiness__item--${item.status.toLowerCase()}`}
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
