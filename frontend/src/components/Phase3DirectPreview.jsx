import { useState } from "react";

const API_BASE = "http://127.0.0.1:8000";

function cleanStationCode(value) {
  return value.trim().toUpperCase();
}

function displayValue(value, fallback = "—") {
  if (value === undefined || value === null || value === "") {
    return fallback;
  }

  return String(value);
}

export default function Phase3DirectPreview() {
  const [source, setSource] = useState("LTT");
  const [destination, setDestination] = useState("VVH");
  const [state, setState] = useState({
    loading: false,
    error: "",
    data: null,
  });

  async function searchDirectRoutes(event) {
    event.preventDefault();

    const sourceCode = cleanStationCode(source);
    const destinationCode = cleanStationCode(destination);

    if (!sourceCode || !destinationCode) {
      setState({
        loading: false,
        error: "Enter both source and destination station codes.",
        data: null,
      });
      return;
    }

    setState({
      loading: true,
      error: "",
      data: null,
    });

    try {
      const params = new URLSearchParams({
        source: sourceCode,
        destination: destinationCode,
        limit: "8",
      });

      const response = await fetch(`${API_BASE}/staging/direct?${params.toString()}`);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();

      setState({
        loading: false,
        error: "",
        data,
      });
    } catch (error) {
      setState({
        loading: false,
        error: error instanceof Error ? error.message : "Unable to reach staging direct API",
        data: null,
      });
    }
  }

  const routes = state.data?.routes || [];

  return (
    <section className="phase3-direct-preview-card">
      <div className="phase3-direct-preview-card__header">
        <div>
          <p className="phase3-direct-preview-card__eyebrow">Phase 3 Live Preview</p>
          <h2>Staging Direct Train Search</h2>
        </div>
        <span className="phase3-direct-preview-card__badge">Read-only</span>
      </div>

      <form className="phase3-direct-preview-form" onSubmit={searchDirectRoutes}>
        <label>
          <span>Source</span>
          <input
            value={source}
            onChange={(event) => setSource(event.target.value.toUpperCase())}
            placeholder="LTT"
            maxLength={10}
          />
        </label>

        <label>
          <span>Destination</span>
          <input
            value={destination}
            onChange={(event) => setDestination(event.target.value.toUpperCase())}
            placeholder="VVH"
            maxLength={10}
          />
        </label>

        <button type="submit" disabled={state.loading}>
          {state.loading ? "Searching..." : "Search staging trains"}
        </button>
      </form>

      <p className="phase3-direct-preview-card__hint">
        Default sample uses LTT → VVH because this pair is already verified in staging smoke tests.
      </p>

      {state.error && (
        <p className="phase3-direct-preview-card__message error">
          {state.error}
        </p>
      )}

      {state.data && !state.error && (
        <div className="phase3-direct-preview-results">
          <div className="phase3-direct-preview-summary">
            <strong>
              {state.data.count} direct staging result{state.data.count === 1 ? "" : "s"}
            </strong>
            <span>
              {state.data.source} → {state.data.destination}
            </span>
          </div>

          {routes.length === 0 && (
            <p className="phase3-direct-preview-card__message">
              No direct staging train found for this station pair yet.
            </p>
          )}

          {routes.length > 0 && (
            <div className="phase3-direct-preview-list">
              {routes.map((route, index) => (
                <article
                  className="phase3-direct-preview-route"
                  key={`${route.train_number}-${route.source_sequence}-${route.destination_sequence}-${index}`}
                >
                  <div>
                    <strong>{displayValue(route.train_number)}</strong>
                    <span>{displayValue(route.train_name, "Train name unavailable")}</span>
                  </div>

                  <div>
                    <span>Type</span>
                    <strong>{displayValue(route.train_type)}</strong>
                  </div>

                  <div>
                    <span>Stops</span>
                    <strong>{displayValue(route.stop_count)}</strong>
                  </div>

                  <div>
                    <span>Departure</span>
                    <strong>{displayValue(route.departure)}</strong>
                  </div>

                  <div>
                    <span>Arrival</span>
                    <strong>{displayValue(route.arrival)}</strong>
                  </div>
                </article>
              ))}
            </div>
          )}

          <p className="phase3-direct-preview-card__message">
            Database write skipped. Production railway tables protected.
          </p>
        </div>
      )}
    </section>
  );
}
