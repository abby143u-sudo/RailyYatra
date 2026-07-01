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

function routeLabel(routeType) {
  if (routeType === "direct") {
    return "Direct";
  }

  if (routeType === "one_transfer") {
    return "One transfer";
  }

  return displayValue(routeType, "Route");
}

export default function Phase3RouteSearchPreview() {
  const [source, setSource] = useState("LTT");
  const [destination, setDestination] = useState("VVH");
  const [sourceSuggestions, setSourceSuggestions] = useState([]);
  const [destinationSuggestions, setDestinationSuggestions] = useState([]);
  const [state, setState] = useState({
    loading: false,
    error: "",
    data: null,
  });

  async function loadStationSuggestions(value, target) {
    const query = cleanStationCode(value);

    if (query.length < 2) {
      if (target === "source") {
        setSourceSuggestions([]);
      } else {
        setDestinationSuggestions([]);
      }

      return;
    }

    try {
      const params = new URLSearchParams({
        q: query,
        limit: "6",
      });

      const response = await fetch(`${API_BASE}/staging/stations?${params.toString()}`);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      const stations = data.stations || [];

      if (target === "source") {
        setSourceSuggestions(stations);
      } else {
        setDestinationSuggestions(stations);
      }
    } catch {
      if (target === "source") {
        setSourceSuggestions([]);
      } else {
        setDestinationSuggestions([]);
      }
    }
  }

  function chooseStation(station, target) {
    const code = station.station_code || "";

    if (target === "source") {
      setSource(code);
      setSourceSuggestions([]);
    } else {
      setDestination(code);
      setDestinationSuggestions([]);
    }
  }

  async function searchRoutes(event) {
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

      const response = await fetch(`${API_BASE}/staging/search?${params.toString()}`);

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
        error: error instanceof Error ? error.message : "Unable to reach staging route engine",
        data: null,
      });
    }
  }

  const routes = state.data?.routes || [];

  return (
    <section className="phase3-route-search-card">
      <div className="phase3-route-search-card__header">
        <div>
          <p className="phase3-route-search-card__eyebrow">Phase 3 Engine</p>
          <h2>Real Staging Route Search</h2>
        </div>
        <span className="phase3-route-search-card__badge">Direct + Transfer</span>
      </div>

      <form className="phase3-route-search-form" onSubmit={searchRoutes}>
        <label className="phase3-route-search-station-field">
          <span>Source</span>
          <input
            value={source}
            onChange={(event) => {
              const value = event.target.value.toUpperCase();
              setSource(value);
              loadStationSuggestions(value, "source");
            }}
            placeholder="LTT"
            maxLength={30}
          />

          {sourceSuggestions.length > 0 && (
            <div className="phase3-route-search-suggestions">
              {sourceSuggestions.map((station) => (
                <button
                  type="button"
                  key={`source-${station.station_code}`}
                  onClick={() => chooseStation(station, "source")}
                >
                  <strong>{station.station_code}</strong>
                  <span>{station.station_name || "Station name unavailable"}</span>
                </button>
              ))}
            </div>
          )}
        </label>

        <label className="phase3-route-search-station-field">
          <span>Destination</span>
          <input
            value={destination}
            onChange={(event) => {
              const value = event.target.value.toUpperCase();
              setDestination(value);
              loadStationSuggestions(value, "destination");
            }}
            placeholder="VVH"
            maxLength={30}
          />

          {destinationSuggestions.length > 0 && (
            <div className="phase3-route-search-suggestions">
              {destinationSuggestions.map((station) => (
                <button
                  type="button"
                  key={`destination-${station.station_code}`}
                  onClick={() => chooseStation(station, "destination")}
                >
                  <strong>{station.station_code}</strong>
                  <span>{station.station_name || "Station name unavailable"}</span>
                </button>
              ))}
            </div>
          )}
        </label>

        <button type="submit" disabled={state.loading}>
          {state.loading ? "Searching..." : "Search real staging routes"}
        </button>
      </form>

      <p className="phase3-route-search-card__hint">
        Type station code or name. Suggestions come from the real staging station table.
      </p>

      {state.error && (
        <p className="phase3-route-search-card__message error">
          {state.error}
        </p>
      )}

      {state.data && !state.error && (
        <div className="phase3-route-search-results">
          <div className="phase3-route-search-summary">
            <div>
              <span>Total routes</span>
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

          {routes.length === 0 && (
            <p className="phase3-route-search-card__message">
              No staging route found for this pair yet.
            </p>
          )}

          {routes.length > 0 && (
            <div className="phase3-route-search-list">
              {routes.map((route, index) => (
                <article
                  className="phase3-route-search-route"
                  key={`${route.route_type}-${route.transfer_station || "direct"}-${index}`}
                >
                  <div className="phase3-route-search-route__top">
                    <div>
                      <span className="phase3-route-search-pill">
                        {routeLabel(route.route_type)}
                      </span>
                      <h3>
                        {state.data.source} → {route.transfer_station ? `${route.transfer_station} → ` : ""}
                        {state.data.destination}
                      </h3>
                    </div>

                    <div className="phase3-route-search-score">
                      <span>Score</span>
                      <strong>{displayValue(route.score)}</strong>
                    </div>
                  </div>

                  <div className="phase3-route-search-meta">
                    <div>
                      <span>Total stops</span>
                      <strong>{displayValue(route.total_stop_count)}</strong>
                    </div>
                    <div>
                      <span>Total distance</span>
                      <strong>{displayValue(route.total_distance)} km</strong>
                    </div>
                    <div>
                      <span>Legs</span>
                      <strong>{route.legs?.length || 0}</strong>
                    </div>
                  </div>

                  <div className="phase3-route-search-legs">
                    {(route.legs || []).map((leg, legIndex) => (
                      <div
                        className="phase3-route-search-leg"
                        key={`${leg.train_number}-${leg.from_station_code}-${leg.to_station_code}-${legIndex}`}
                      >
                        <div>
                          <strong>{displayValue(leg.train_number)}</strong>
                          <span>{displayValue(leg.train_name, "Train name unavailable")}</span>
                        </div>

                        <div>
                          <span>Route</span>
                          <strong>
                            {displayValue(leg.from_station_code)} → {displayValue(leg.to_station_code)}
                          </strong>
                        </div>

                        <div>
                          <span>Departure</span>
                          <strong>{displayValue(leg.departure)}</strong>
                        </div>

                        <div>
                          <span>Arrival</span>
                          <strong>{displayValue(leg.arrival)}</strong>
                        </div>
                      </div>
                    ))}
                  </div>

                  {route.warnings?.length > 0 && (
                    <p className="phase3-route-search-card__message warning">
                      Warnings: {route.warnings.join(", ")}
                    </p>
                  )}
                </article>
              ))}
            </div>
          )}

          <p className="phase3-route-search-card__message">
            Database write skipped. Production railway tables protected.
          </p>
        </div>
      )}
    </section>
  );
}
