import { useState } from "react";
import { API_BASE } from "../config/api.js";

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

  function handleStationInputChange(value, target) {
    const normalizedValue = value.toUpperCase();

    if (target === "source") {
      setSource(normalizedValue);
    } else {
      setDestination(normalizedValue);
    }

    loadStationSuggestions(normalizedValue, target);
  }

  function handleStationInputFocus(target) {
    if (target === "source") {
      loadStationSuggestions(source, "source");
    } else {
      loadStationSuggestions(destination, "destination");
    }
  }

  function handleStationInputKeyUp(event, target) {
    const browseKeys = ["Backspace", "Delete", "ArrowDown", "ArrowUp"];

    if (browseKeys.includes(event.key)) {
      loadStationSuggestions(event.currentTarget.value, target);
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

  async function toggleTrainStops(
    trainNumber,
    fromSequence,
    toSequence
  ) {
    const key =
      `${trainNumber}-${fromSequence}-${toSequence}`;

    const existing = stopDetails[key];

    if (existing?.open) {
      setStopDetails((current) => ({
        ...current,
        [key]: {
          ...current[key],
          open: false,
        },
      }));
      return;
    }

    if (existing?.stops?.length) {
      setStopDetails((current) => ({
        ...current,
        [key]: {
          ...current[key],
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
      const response = await fetch(
        `${API_BASE}/staging/trains/` +
        `${encodeURIComponent(trainNumber)}/stops?limit=500`
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      const allStops = Array.isArray(data.stops)
        ? data.stops
        : [];

      const start = Number(fromSequence);
      const end = Number(toSequence);

      const rangeAvailable =
        Number.isFinite(start) &&
        Number.isFinite(end);

      const visibleStops = rangeAvailable
        ? allStops.filter((stop) => {
            const sequence = Number(
              stop.stop_sequence
            );

            return (
              Number.isFinite(sequence) &&
              sequence >= start &&
              sequence <= end
            );
          })
        : allStops;

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
          error:
            error instanceof Error
              ? error.message
              : "Unable to load train stops",
          open: true,
          stops: [],
        },
      }));
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
        <label className="phase4-recommend-station-field">
          <span>Source</span>
          <input
            value={source}
            onChange={(event) => handleStationInputChange(event.target.value, "source")}
            onFocus={() => handleStationInputFocus("source")}
            onKeyUp={(event) => handleStationInputKeyUp(event, "source")}
            placeholder="LTT"
            maxLength={30}
          />

          {sourceSuggestions.length > 0 && (
            <div className="phase4-recommend-suggestions">
              {sourceSuggestions.map((station) => (
                <button
                  type="button"
                  key={`recommend-source-${station.station_code}`}
                  onClick={() => chooseStation(station, "source")}
                >
                  <strong>{station.station_code}</strong>
                  <span>{station.station_name || "Station name unavailable"}</span>
                </button>
              ))}
            </div>
          )}
        </label>

        <label className="phase4-recommend-station-field">
          <span>Destination</span>
          <input
            value={destination}
            onChange={(event) => handleStationInputChange(event.target.value, "destination")}
            onFocus={() => handleStationInputFocus("destination")}
            onKeyUp={(event) => handleStationInputKeyUp(event, "destination")}
            placeholder="VVH"
            maxLength={30}
          />

          {destinationSuggestions.length > 0 && (
            <div className="phase4-recommend-suggestions">
              {destinationSuggestions.map((station) => (
                <button
                  type="button"
                  key={`recommend-destination-${station.station_code}`}
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
          {state.loading ? "Ranking..." : "Get recommendations"}
        </button>
      </form>

      <p className="phase4-recommend-card__hint">
        Type station code or name. Suggestions come from the real staging station table.
      </p>

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

                  {route.legs?.[0] && (
                    <div className="phase4-primary-leg-preview">
                      <div>
                        <span>Primary train</span>
                        <strong>
                          {displayValue(route.legs[0].train_number)} ·{" "}
                          {displayValue(
                            route.legs[0].train_name,
                            "Train name unavailable"
                          )}
                        </strong>
                      </div>

                      <div>
                        <span>Journey time</span>
                        <strong>
                          {displayValue(route.legs[0].departure)} →{" "}
                          {displayValue(route.legs[0].arrival)}
                        </strong>
                      </div>
                    </div>
                  )}

                  <details className="phase4-journey-details">
                    <summary>
                      <span>Journey details</span>
                      <small>
                        {(route.legs || []).length}{" "}
                        {(route.legs || []).length === 1
                          ? "train leg"
                          : "train legs"}{" "}
                        · {displayValue(route.transfer_safety?.label)}
                      </small>
                    </summary>

                    <div className="phase4-journey-details__content">
                      <div className="phase4-safety-detail">
                        <span>Transfer safety</span>
                        <strong>
                          {displayValue(route.transfer_safety?.label)}
                        </strong>
                        <p>
                          {displayValue(
                            route.transfer_safety?.reason,
                            "Transfer safety details unavailable."
                          )}
                        </p>

                        {route.route_type === "one_transfer" &&
                          route.transfer_connection && (
                            <div
                              className={
                                "phase4-transfer-connection " +
                                `phase4-transfer-connection--${
                                  route.transfer_connection
                                    .risk_level || "unknown"
                                }`
                              }
                            >
                              <div>
                                <span>Transfer station</span>
                                <strong>
                                  {displayValue(
                                    route.transfer_station
                                  )}
                                </strong>
                              </div>

                              <div>
                                <span>First train arrival</span>
                                <strong>
                                  {displayValue(
                                    route.transfer_connection
                                      .arrival
                                  )}
                                </strong>
                              </div>

                              <div>
                                <span>Next train departure</span>
                                <strong>
                                  {displayValue(
                                    route.transfer_connection
                                      .departure
                                  )}
                                </strong>
                              </div>

                              <div>
                                <span>Estimated wait</span>
                                <strong>
                                  {displayValue(
                                    route.transfer_connection
                                      .wait_label,
                                    "Unavailable"
                                  )}
                                </strong>
                              </div>

                              {route.transfer_connection
                                .rolls_to_next_day && (
                                <p>
                                  Next-day departure assumed
                                  from timetable clock values.
                                </p>
                              )}

                              <small>
                                Preview estimate only. Actual
                                connection depends on journey
                                date, operating days and delays.
                              </small>
                            </div>
                          )}
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
                        {(route.legs || []).map((leg, index) => {
                          const stopKey =
                            `${leg.train_number}-` +
                            `${leg.from_sequence}-` +
                            `${leg.to_sequence}`;

                          const details =
                            stopDetails[stopKey];

                          return (
                            <div
                              className="phase4-leg-block"
                              key={
                                `${route.recommendation_rank}-` +
                                `${leg.train_number}-${index}`
                              }
                            >
                              <div className="phase4-leg-row">
                                <div>
                                  <span>Train</span>
                                  <strong>
                                    {displayValue(
                                      leg.train_number
                                    )}
                                  </strong>
                                </div>

                                <div>
                                  <span>Name</span>
                                  <strong>
                                    {displayValue(
                                      leg.train_name,
                                      "Train name unavailable"
                                    )}
                                  </strong>
                                </div>

                                <div>
                                  <span>Route</span>
                                  <strong>
                                    {displayValue(
                                      leg.from_station_code
                                    )}{" "}
                                    →{" "}
                                    {displayValue(
                                      leg.to_station_code
                                    )}
                                  </strong>
                                </div>

                                <div>
                                  <span>Time</span>
                                  <strong>
                                    {displayValue(
                                      leg.departure
                                    )}{" "}
                                    →{" "}
                                    {displayValue(
                                      leg.arrival
                                    )}
                                  </strong>
                                </div>

                                <div>
                                  <span>Distance</span>
                                  <strong>
                                    {displayValue(
                                      leg.distance
                                    )}{" "}
                                    km
                                  </strong>
                                </div>

                                <div>
                                  <span>Stops</span>
                                  <strong>
                                    {displayValue(
                                      leg.stop_count
                                    )}
                                  </strong>
                                </div>
                              </div>

                              <button
                                type="button"
                                className="phase4-stop-toggle"
                                onClick={() =>
                                  toggleTrainStops(
                                    leg.train_number,
                                    leg.from_sequence,
                                    leg.to_sequence
                                  )
                                }
                                disabled={
                                  !leg.train_number ||
                                  details?.loading
                                }
                              >
                                {details?.loading
                                  ? "Loading stops..."
                                  : details?.open
                                    ? "Hide intermediate stops"
                                    : "View intermediate stops"}
                              </button>

                              {details?.open && (
                                <div className="phase4-stop-panel">
                                  {details.error && (
                                    <p className="phase4-stop-error">
                                      Could not load stops:{" "}
                                      {details.error}
                                    </p>
                                  )}

                                  {!details.loading &&
                                    !details.error &&
                                    details.stops.length === 0 && (
                                      <p className="phase4-stop-empty">
                                        No stop details found for
                                        this train leg.
                                      </p>
                                    )}

                                  {details.stops.length > 0 && (
                                    <div className="phase4-stop-list">
                                      {details.stops.map(
                                        (stop, stopIndex) => {
                                          const isBoarding =
                                            stopIndex === 0;

                                          const isDestination =
                                            stopIndex ===
                                            details.stops.length -
                                              1;

                                          return (
                                            <div
                                              className={
                                                "phase4-stop-row"
                                              }
                                              key={
                                                `${stop.station_code}-` +
                                                `${stop.stop_sequence}-` +
                                                stopIndex
                                              }
                                            >
                                              <div className="phase4-stop-marker">
                                                <span />
                                              </div>

                                              <div className="phase4-stop-station">
                                                <strong>
                                                  {displayValue(
                                                    stop.station_code
                                                  )}
                                                </strong>

                                                <small>
                                                  Stop{" "}
                                                  {displayValue(
                                                    stop.stop_sequence
                                                  )}
                                                  {isBoarding
                                                    ? " · Boarding"
                                                    : ""}
                                                  {isDestination
                                                    ? " · Destination"
                                                    : ""}
                                                </small>
                                              </div>

                                              <div>
                                                <span>Arrival</span>
                                                <strong>
                                                  {displayValue(
                                                    stop.arrival
                                                  )}
                                                </strong>
                                              </div>

                                              <div>
                                                <span>Departure</span>
                                                <strong>
                                                  {displayValue(
                                                    stop.departure
                                                  )}
                                                </strong>
                                              </div>

                                              <div>
                                                <span>Day</span>
                                                <strong>
                                                  Day{" "}
                                                  {Number(
                                                    stop.day_offset ||
                                                      0
                                                  ) + 1}
                                                </strong>
                                              </div>
                                            </div>
                                          );
                                        }
                                      )}
                                    </div>
                                  )}
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>

                      <div className="phase4-booking-warning">
                        <strong>
                          Live booking not connected yet.
                        </strong>
                        <span>
                          {route.booking_status?.note}
                        </span>
                      </div>
                    </div>
                  </details>
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
