import { useEffect, useState } from "react";
import { API_BASE } from "../config/api.js";

function formatCount(value) {
  if (value === undefined || value === null) {
    return "0";
  }

  return Number(value).toLocaleString("en-IN");
}

export default function Phase3StagingCard() {
  const [state, setState] = useState({
    loading: true,
    error: "",
    data: null,
  });

  useEffect(() => {
    let cancelled = false;

    async function loadHealth() {
      try {
        const response = await fetch(`${API_BASE}/staging/health`);

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
            error: error instanceof Error ? error.message : "Unable to reach staging API",
            data: null,
          });
        }
      }
    }

    loadHealth();

    return () => {
      cancelled = true;
    };
  }, []);

  const counts = state.data?.counts || {};
  const ready = state.data?.status === "ready";

  return (
    <section className="phase3-staging-card">
      <div className="phase3-staging-card__header">
        <div>
          <p className="phase3-staging-card__eyebrow">Phase 3</p>
          <h2>Real Railway Data Staging</h2>
        </div>

        <span className={`phase3-staging-card__badge ${ready ? "ready" : "not-ready"}`}>
          {state.loading ? "Checking" : ready ? "Ready" : "Not Ready"}
        </span>
      </div>

      {state.loading && (
        <p className="phase3-staging-card__message">
          Checking staging railway data health...
        </p>
      )}

      {!state.loading && state.error && (
        <p className="phase3-staging-card__message error">
          Staging API not reachable: {state.error}
        </p>
      )}

      {!state.loading && !state.error && (
        <>
          <div className="phase3-staging-card__grid">
            <div>
              <span>Stations</span>
              <strong>{formatCount(counts.staging_stations)}</strong>
            </div>
            <div>
              <span>Trains</span>
              <strong>{formatCount(counts.staging_trains)}</strong>
            </div>
            <div>
              <span>Stops</span>
              <strong>{formatCount(counts.staging_train_stops)}</strong>
            </div>
          </div>

          <p className="phase3-staging-card__message">
            Read-only staging API connected. Production railway tables protected.
          </p>
        </>
      )}
    </section>
  );
}
