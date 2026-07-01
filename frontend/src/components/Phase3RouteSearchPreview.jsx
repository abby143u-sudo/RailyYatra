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
  const [stopDetails, setStopDetails] = useState({});
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

    setStopDetails({});
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

      const response = await fetch(`${API_BASE}/search-v2?${params.toString()}`);

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
        error: error instanceof Error ? error.message : "Unable to reach search-v2 route engine",
        data: null,
      });
    }
  }

  async function toggleTrainStops(trainNumber, fromSequence, toSequence) {
    const key = `${trainNumber}-${fromSequence}-${toSequence}`;
    const existing = stopDetails[key];

    if (existing?.open) {
      setStopDetails((current) => ({
        ...current,
        [key]: {
          ...existing,
          open: false,
        },
      }));
      return;
    }

    if (existing?.stops?.length) {
      setStopDetails((current) => ({
        ...current,
        [key]: {
          ...existing,
          open: true,
        },
      }));
      return;
    }

    setStopDetails((current) => ({
      ...current,
      [key]: {
        loading: true,
        error: "",
        open: true,
        stops: [],
      },
    }));

    try {
      const response = await fetch(`${API_BASE}/staging/trains/${trainNumber}/stops?limit=500`);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      const allStops = data.stops || [];
      const start = Number(fromSequence);
      const end = Number(toSequence);

      const visibleStops = allStops.filter((stop) => {
        const sequence = Number(stop.stop_sequence);
        return sequence >= start && sequence <= end;
      });

      setStopDetails((current) => ({
        ...current,
        [key]: {
          loading: false,
          error: "",
          open: true,
          stops: visibleStops,
        },
      }));
    } catch (error) {
      setStopDetails((current) => ({
        ...current,
        [key]: {
          loading: false,
          error: error instanceof Error ? error.message : "Unable to fetch train stops",
          open: true,
          stops: [],
        },
      }));
    }
  }

  const routes = state.data?.routes || [];

  return (
    <section className="phase3-route-search-card">
      <div className="phase3-route-search-card__header">
        <div>
          <p className="phase3-route-search-card__eyebrow">Search v2</p>
          <h2>Production Candidate Route Search</h2>
        </div>
        <span className="phase3-route-search-card__badge">/search-v2</span>
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
                    {(route.legs || []).map((leg, legIndex) => {
                      const stopKey = `${leg.train_number}-${leg.from_sequence}-${leg.to_sequence}`;
                      const details = stopDetails[stopKey];

                      return (
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

                          <div className="phase3-route-search-stop-action">
                            <button
                              type="button"
                              onClick={() => toggleTrainStops(leg.train_number, leg.from_sequence, leg.to_sequence)}
                            >
                              {details?.open ? "Hide stops" : "View stops"}
                            </button>
                          </div>

                          {details?.open && (
                            <div className="phase3-route-search-stop-panel">
                              {details.loading && <p>Loading train stops...</p>}

                              {details.error && (
                                <p className="phase3-route-search-card__message error">
                                  {details.error}
                                </p>
                              )}

                              {!details.loading && !details.error && details.stops.length === 0 && (
                                <p>No stop details found for this leg.</p>
                              )}

                              {!details.loading && !details.error && details.stops.length > 0 && (
                                <div className="phase3-route-search-stop-list">
                                  {details.stops.map((stop) => (
                                    <div
                                      className="phase3-route-search-stop-row"
                                      key={`${leg.train_number}-${stop.station_code}-${stop.stop_sequence}`}
                                    >
                                      <span>{stop.stop_sequence}</span>
                                      <strong>{stop.station_code}</strong>
                                      <span>Arr: {displayValue(stop.arrival)}</span>
                                      <span>Dep: {displayValue(stop.departure)}</span>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })}
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
