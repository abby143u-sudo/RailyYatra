import { useEffect, useState } from "react";
import { API_BASE } from "../config/api.js";

function statusLabel(value) {
  if (value === true) {
    return "Yes";
  }

  if (value === false) {
    return "No";
  }

  return String(value ?? "—");
}

export default function Phase5ProductStatusPanel() {
  const [state, setState] = useState({
    loading: true,
    error: "",
    data: null,
  });

  useEffect(() => {
    let cancelled = false;

    async function loadProductStatus() {
      try {
        const response = await fetch(`${API_BASE}/product/status`);

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        if (!cancelled) {
          setState({
            loading: false,
            error: "",
            data,
          });
        }
      } catch (error) {
        if (!cancelled) {
          setState({
            loading: false,
            error: error instanceof Error ? error.message : "Unable to reach product status API",
            data: null,
          });
        }
      }
    }

    loadProductStatus();

    return () => {
      cancelled = true;
    };
  }, []);

  const data = state.data;
  const engines = data?.available_engines || {};
  const live = data?.live_integrations || {};
  const flags = data?.public_beta_flags || {};
  const safety = data?.safety || {};

  return (
    <section className="phase5-product-status-card">
      <div className="phase5-product-status-card__header">
        <div>
          <p className="phase5-product-status-card__eyebrow">Public Beta</p>
          <h2>RailYatra Release Status</h2>
        </div>

        <span className="phase5-product-status-card__badge">/product/status</span>
      </div>

      {state.loading && (
        <p className="phase5-product-status-card__message">
          Checking RailYatra product readiness...
        </p>
      )}

      {!state.loading && state.error && (
        <p className="phase5-product-status-card__message error">
          Product status API not reachable: {state.error}
        </p>
      )}

      {!state.loading && data && !state.error && (
        <>
          <div className="phase5-status-hero">
            <div>
              <span>Product</span>
              <strong>{data.product_name}</strong>
            </div>
            <div>
              <span>Status</span>
              <strong>{data.status}</strong>
            </div>
            <div>
              <span>Mode</span>
              <strong>{data.current_mode}</strong>
            </div>
            <div>
              <span>Version</span>
              <strong>{data.version || data.phase}</strong>
            </div>
          </div>

          <div className="phase5-status-section">
            <h3>Available engines</h3>
            <div className="phase5-engine-grid">
              {Object.entries(engines).map(([key, engine]) => (
                <article className="phase5-engine-card" key={key}>
                  <span>{engine.endpoint}</span>
                  <strong>{engine.status}</strong>
                  <p>{engine.purpose}</p>
                </article>
              ))}
            </div>
          </div>

          <div className="phase5-status-section">
            <h3>Real data layer</h3>
            <div className="phase5-status-grid">
              <div>
                <span>Stations</span>
                <strong>{data.data_layer?.stations?.toLocaleString?.("en-IN")}</strong>
              </div>
              <div>
                <span>Trains</span>
                <strong>{data.data_layer?.trains?.toLocaleString?.("en-IN")}</strong>
              </div>
              <div>
                <span>Train stops</span>
                <strong>{data.data_layer?.train_stops?.toLocaleString?.("en-IN")}</strong>
              </div>
              <div>
                <span>Read only</span>
                <strong>{statusLabel(data.data_layer?.read_only)}</strong>
              </div>
            </div>
          </div>

          <div className="phase5-status-section">
            <h3>Live integrations</h3>
            <div className="phase5-live-grid">
              {Object.entries(live).map(([key, value]) => (
                <div className={value ? "phase5-live-item live" : "phase5-live-item blocked"} key={key}>
                  <span>{key.replaceAll("_", " ")}</span>
                  <strong>{statusLabel(value)}</strong>
                </div>
              ))}
            </div>
            <p className="phase5-product-status-card__message warning">
              Live booking, PNR, fare, availability, payment and cancellation are not connected yet.
            </p>
          </div>

          <div className="phase5-status-section">
            <h3>Public beta flags</h3>
            <div className="phase5-status-grid">
              {Object.entries(flags).map(([key, value]) => (
                <div key={key}>
                  <span>{key.replaceAll("_", " ")}</span>
                  <strong>{statusLabel(value)}</strong>
                </div>
              ))}
            </div>
          </div>

          <div className="phase5-status-section">
            <h3>Safety</h3>
            <div className="phase5-status-grid">
              {Object.entries(safety).map(([key, value]) => (
                <div key={key}>
                  <span>{key.replaceAll("_", " ")}</span>
                  <strong>{statusLabel(value)}</strong>
                </div>
              ))}
            </div>
          </div>

          <p className="phase5-product-status-card__message">
            RailYatra is live as a route-recommendation public beta. Live ticketing and payment claims remain blocked.
          </p>
        </>
      )}
    </section>
  );
}
