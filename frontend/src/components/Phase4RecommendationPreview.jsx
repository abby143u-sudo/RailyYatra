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

function confidenceLabel(level) {
  if (level === "very_high") {
    return "Very high";
  }

  if (level === "high") {
    return "High";
  }

  if (level === "medium") {
    return "Medium";
  }

  return "Low";
}

function routeLabel(routeType) {
  if (routeType === "direct") {
    return "Direct";
  }

  if (routeType === "one_transfer") {
    return "One transfer";
  }

  return displayValue(routeType, "Route");
}

export default function Phase4RecommendationPreview() {
  const [source, setSource] = useState("LTT");
  const [destination, setDestination] = useState("VVH");
  const [state, setState] = useState({
    loading: false,
    error: "",
    data: null,
  });

  async function loadRecommendations(event) {
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
        direct_limit: "5",
        transfer_limit: "2",
      });

      const response = await fetch(`${API_BASE}/recommend-v2?${params.toString()}`);

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
        error: error instanceof Error ? error.message : "Unable to reach recommend-v2 engine",
        data: null,
      });
    }
  }

  const recommendations = state.data?.recommendations || [];
  const best = state.data?.summary?.best_available;

  return (
    <section className="phase4-recommend-card">
      <div className="phase4-recommend-card__header">
        <div>
          <p className="phase4-recommend-card__eyebrow">Phase 4</p>
          <h2>Recommendation v2 Preview</h2>
        </div>

        <span className="phase4-recommend-card__badge">/recommend-v2</span>
      </div>

      <form className="phase4-recommend-form" onSubmit={loadRecommendations}>
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
          {state.loading ? "Ranking..." : "Get recommendations"}
        </button>
      </form>

      <p className="phase4-recommend-card__hint">
        This uses /recommend-v2 with confidence, transfer safety, reasons, and booking readiness labels.
      </p>

      {state.error && (
        <p className="phase4-recommend-card__message error">
          {state.error}
        </p>
      )}

      {state.data && !state.error && (
        <div className="phase4-recommend-results">
          <div className="phase4-recommend-summary">
            <div>
              <span>Total recommendations</span>
              <strong>{state.data.count}</strong>
            </div>
            <div>
              <span>Direct</span>
              <strong>{state.data.direct_count}</strong>
            </div>
            <div>
              <span>One transfer</span>
              <strong>{state.data.one_transfer_count}</strong>
            </div>
          </div>

          {best && (
            <div className="phase4-best-box">
              <span>Best available</span>
              <strong>
                #{best.recommendation_rank} · {routeLabel(best.route_type)} · Score {best.confidence?.score}
              </strong>
            </div>
          )}

          {recommendations.length === 0 && (
            <p className="phase4-recommend-card__message">
              No recommendation found for this pair yet.
            </p>
          )}

          {recommendations.length > 0 && (
            <div className="phase4-recommend-list">
              {recommendations.map((route) => (
                <article
                  className="phase4-recommend-route"
                  key={`${route.recommendation_rank}-${route.route_type}-${route.transfer_station || "direct"}`}
                >
                  <div className="phase4-recommend-route__top">
                    <div>
                      <span className="phase4-rank-pill">Rank #{route.recommendation_rank}</span>
                      <h3>
                        {state.data.source} → {route.transfer_station ? `${route.transfer_station} → ` : ""}
                        {state.data.destination}
                      </h3>
                    </div>

                    <div className="phase4-score-box">
                      <span>{confidenceLabel(route.confidence?.level)}</span>
                      <strong>{displayValue(route.confidence?.score)}</strong>
                    </div>
                  </div>

                  <div className="phase4-recommend-meta">
                    <div>
                      <span>Route type</span>
                      <strong>{routeLabel(route.route_type)}</strong>
                    </div>
                    <div>
                      <span>Safety</span>
                      <strong>{displayValue(route.transfer_safety?.label)}</strong>
                    </div>
                    <div>
                      <span>Stops</span>
                      <strong>{displayValue(route.total_stop_count)}</strong>
                    </div>
                    <div>
                      <span>Distance</span>
                      <strong>{displayValue(route.total_distance)} km</strong>
                    </div>
                  </div>

                  <div className="phase4-reasons-box">
                    <span>Why recommended</span>
                    <ul>
                      {(route.reasons || []).map((reason) => (
                        <li key={reason}>{reason}</li>
                      ))}
                    </ul>
                  </div>

                  <div className="phase4-leg-list">
                    {(route.legs || []).map((leg, index) => (
                      <div
                        className="phase4-leg-row"
                        key={`${route.recommendation_rank}-${leg.train_number}-${index}`}
                      >
                        <div>
                          <span>Train</span>
                          <strong>{displayValue(leg.train_number)}</strong>
                        </div>
                        <div>
                          <span>Name</span>
                          <strong>{displayValue(leg.train_name, "Train name unavailable")}</strong>
                        </div>
                        <div>
                          <span>Route</span>
                          <strong>
                            {displayValue(leg.from_station_code)} → {displayValue(leg.to_station_code)}
                          </strong>
                        </div>
                        <div>
                          <span>Time</span>
                          <strong>
                            {displayValue(leg.departure)} → {displayValue(leg.arrival)}
                          </strong>
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="phase4-booking-warning">
                    <strong>Live booking not connected yet.</strong>
                    <span>{route.booking_status?.note}</span>
                  </div>
                </article>
              ))}
            </div>
          )}

          <p className="phase4-recommend-card__message">
            Database write skipped. Production railway tables protected. Legacy /search unchanged.
          </p>
        </div>
      )}
    </section>
  );
}
