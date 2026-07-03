import { useEffect, useState } from "react";
import { apiUrl } from "../config/api.js";

const demoRoutes = [
  {
    label: "Delhi demo route",
    source: "DSNR",
    destination: "TPKR",
    note: "Use this for fast public demo testing.",
  },
  {
    label: "Patna route demo",
    source: "PNBE",
    destination: "NDLS",
    note: "Use this to demonstrate route recommendation logic.",
  },
];

const boundaries = [
  "Live ticket booking is not connected yet.",
  "Payment is not connected yet.",
  "PNR is not connected yet.",
  "Live fare and live seat availability are not connected yet.",
  "RailYatra currently recommends railway routes from prepared railway data.",
];

export default function BetaReadinessPanel() {
  const [backendStatus, setBackendStatus] = useState("Checking backend...");
  const [databaseStatus, setDatabaseStatus] = useState("Checking database...");
  const [liveStatusMode, setLiveStatusMode] = useState("Checking live train status readiness...");

  useEffect(() => {
    async function loadStatus() {
      try {
        const health = await fetch(apiUrl("/health"));
        const healthData = await health.json();
        setBackendStatus(healthData.status === "healthy" ? "Backend healthy" : "Backend needs attention");
      } catch {
        setBackendStatus("Backend unavailable");
      }

      try {
        const feedback = await fetch(apiUrl("/feedback/health"));
        const feedbackData = await feedback.json();
        setDatabaseStatus(feedbackData.storage === "postgresql" ? "PostgreSQL connected" : "SQLite fallback active");
      } catch {
        setDatabaseStatus("Database status unavailable");
      }

      try {
        const live = await fetch(apiUrl("/live-status/health"));
        const liveData = await live.json();
        setLiveStatusMode(liveData.real_live_status_enabled ? "Live status provider connected" : "Live status provider pending");
      } catch {
        setLiveStatusMode("Live status API pending");
      }
    }

    loadStatus();
  }, []);

  return (
    <section className="beta-readiness-panel" aria-label="RailYatra beta readiness">
      <div className="beta-readiness-panel__header">
        <span>Beta readiness</span>
        <strong>RailYatra is ready for controlled public demo testing</strong>
        <p>Use this app as a route recommendation preview. It is not a booking, payment, PNR or live availability product yet.</p>
      </div>

      <div className="beta-readiness-panel__status-grid">
        <article><span>Backend</span><strong>{backendStatus}</strong></article>
        <article><span>Persistence</span><strong>{databaseStatus}</strong></article>
        <article><span>Live status</span><strong>{liveStatusMode}</strong></article>
      </div>

      <div className="beta-readiness-panel__content">
        <div>
          <strong>Demo routes</strong>
          <div className="beta-readiness-panel__routes">
            {demoRoutes.map((route) => (
              <article key={`${route.source}-${route.destination}`}>
                <span>{route.label}</span>
                <strong>{route.source} → {route.destination}</strong>
                <p>{route.note}</p>
              </article>
            ))}
          </div>
        </div>

        <div>
          <strong>Public boundary</strong>
          <ul className="beta-readiness-panel__boundary">
            {boundaries.map((item) => <li key={item}>{item}</li>)}
          </ul>
        </div>
      </div>
    </section>
  );
}
