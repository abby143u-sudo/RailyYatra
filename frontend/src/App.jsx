import { useMemo, useState } from "react";
import "./App.css";

const API_BASE = "http://127.0.0.1:8000";

function App() {
  const [source, setSource] = useState("PNBE");
  const [destination, setDestination] = useState("NDLS");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [sourceSuggestions, setSourceSuggestions] = useState([]);
  const [destinationSuggestions, setDestinationSuggestions] = useState([]);
  const [activeFilter, setActiveFilter] = useState("all");
  const [sortMode, setSortMode] = useState("best");
  const [expandedCard, setExpandedCard] = useState(null);

  const allRecommendations = result?.recommendations || [];

  const recommendations = useMemo(() => {
    let filtered = allRecommendations;

    if (activeFilter === "smart") {
      filtered = allRecommendations.filter((item) => item.type === "multi_transfer");
    }

    if (activeFilter === "direct") {
      filtered = allRecommendations.filter((item) => item.type === "direct");
    }

    if (activeFilter === "transfer") {
      filtered = allRecommendations.filter((item) => item.type === "one_transfer");
    }

    const sorted = [...filtered];

    if (sortMode === "best") {
      sorted.sort((a, b) => b.score - a.score);
    }

    if (sortMode === "fastest") {
      sorted.sort(
        (a, b) =>
          getRecommendationDuration(a) - getRecommendationDuration(b)
      );
    }

    if (sortMode === "least_transfers") {
      sorted.sort(
        (a, b) =>
          getRecommendationTransfers(a) - getRecommendationTransfers(b)
      );
    }

    return sorted;
  }, [allRecommendations, activeFilter, sortMode]);

  const bestDirect = useMemo(
    () => allRecommendations.find((item) => item.type === "direct"),
    [allRecommendations]
  );

  const bestTransfer = useMemo(
    () => allRecommendations.find((item) => item.type === "one_transfer"),
    [allRecommendations]
  );

  const bestSmart = useMemo(
    () => allRecommendations.find((item) => item.type === "multi_transfer"),
    [allRecommendations]
  );

  const fastestOption = useMemo(() => {
    if (!allRecommendations.length) return null;

    return [...allRecommendations].sort(
      (a, b) => getRecommendationDuration(a) - getRecommendationDuration(b)
    )[0];
  }, [allRecommendations]);

  const leastTransferOption = useMemo(() => {
    if (!allRecommendations.length) return null;

    return [...allRecommendations].sort(
      (a, b) =>
        getRecommendationTransfers(a) - getRecommendationTransfers(b) ||
        b.score - a.score
    )[0];
  }, [allRecommendations]);

  function cleanStation(value) {
    return value.trim().toUpperCase();
  }

  function swapStations() {
    setSource(destination);
    setDestination(source);
  }

  async function fetchStationSuggestions(value, setter) {
    const query = value.trim();

    if (query.length < 2) {
      setter([]);
      return;
    }

    try {
      const res = await fetch(API_BASE + "/stations?q=" + query + "&limit=8");

      if (!res.ok) return;

      const data = await res.json();
      setter(data.stations || []);
    } catch {
      setter([]);
    }
  }

  function getStationCode(station) {
    return station.station_code || station.code || station.id || "";
  }

  function getStationName(station) {
    return station.station_name || station.name || station.city || "";
  }

  async function searchJourney(e) {
    e.preventDefault();

    const from = cleanStation(source);
    const to = cleanStation(destination);

    if (!from || !to) {
      setError("Please enter both station codes.");
      return;
    }

    if (from === to) {
      setError("Source and destination cannot be same.");
      return;
    }

    setSource(from);
    setDestination(to);
    setLoading(true);
    setError("");
    setResult(null);
    setActiveFilter("all");
    setSortMode("best");
    setExpandedCard(null);

    try {
      const res = await fetch(
        API_BASE + "/search?source=" + from + "&destination=" + to + "&limit=10"
      );

      if (!res.ok) throw new Error("Search failed");

      const data = await res.json();
      setResult(data);
    } catch {
      setError("Backend not connected. Start FastAPI on port 8000.");
    } finally {
      setLoading(false);
    }
  }

  function setQuickRoute(from, to) {
    setSource(from);
    setDestination(to);
  }

  function safeValue(value) {
    if (value === null || value === undefined || value === "None") {
      return "N/A";
    }
    return value;
  }

  function getRecommendationDuration(item) {
    const data = item.data || {};

    if (item.type === "multi_transfer") {
      return data.total_duration_hours || 9999;
    }

    if (item.type === "direct") {
      return data.duration_hours || 9999;
    }

    if (item.type === "one_transfer") {
      return data.total_duration_hours || 9999;
    }

    return 9999;
  }

  function getRecommendationTransfers(item) {
    const data = item.data || {};

    if (item.type === "multi_transfer") {
      return data.transfers || 0;
    }

    if (item.type === "direct") {
      return 0;
    }

    if (item.type === "one_transfer") {
      return 1;
    }

    return 99;
  }

  function toggleDetails(cardId) {
    setExpandedCard(expandedCard === cardId ? null : cardId);
  }

  function getRecommendationTitle(item) {
    if (!item) return "Not available";

    const data = item.data || {};

    if (item.type === "multi_transfer") {
      return data.summary || item.label;
    }

    if (item.type === "direct") {
      return `${data.train_no} ${data.train_name}`;
    }

    if (item.type === "one_transfer") {
      return `${data.first_train} + ${data.second_train}`;
    }

    return item.label || "Journey option";
  }

  function getRecommendationSubtext(item) {
    if (!item) return "";

    const duration = getRecommendationDuration(item);
    const transfers = getRecommendationTransfers(item);

    const durationText = duration === 9999 ? "Duration N/A" : `${duration} hrs`;
    const transferText = transfers === 0 ? "No transfer" : `${transfers} transfer`;

    return `${durationText} · ${transferText} · Score ${item.score}`;
  }

  function renderDirectCard(item, index) {
    const train = item.data;

    const cardId = `direct-${index}`;

    return (
      <div className="journey-card" key={cardId}>
        <div className="card-top">
          <span className="badge direct-badge">Direct</span>
          <strong>Score {item.score}</strong>
        </div>

        <h3>{train.train_no} — {train.train_name}</h3>

        <div className="journey-meta">
          <span>Dep {safeValue(train.departure)}</span>
          <span>Arr {safeValue(train.arrival)}</span>
          <span>{safeValue(train.duration_hours)} hrs</span>
          <span>{safeValue(train.stops)} stops</span>
        </div>

        <button
          type="button"
          className="details-btn"
          onClick={() => toggleDetails(cardId)}
        >
          {expandedCard === cardId ? "Hide details" : "View details"}
        </button>

        {expandedCard === cardId && (
          <div className="details-panel">
            <div className="section-title">Why recommended</div>

            <ul>
              {train.reasons?.map((reason, i) => (
                <li key={i}>✓ {reason}</li>
              ))}
            </ul>

            <div className="detail-grid">
              <span>Train no</span>
              <strong>{train.train_no}</strong>

              <span>Train name</span>
              <strong>{train.train_name}</strong>

              <span>Departure</span>
              <strong>{safeValue(train.departure)}</strong>

              <span>Arrival</span>
              <strong>{safeValue(train.arrival)}</strong>

              <span>Duration</span>
              <strong>{safeValue(train.duration_hours)} hrs</strong>

              <span>Stops</span>
              <strong>{safeValue(train.stops)}</strong>
            </div>
          </div>
        )}
      </div>
    );
  }

  function renderTransferCard(item, index) {
    const route = item.data;

    const cardId = `transfer-${index}`;

    return (
      <div className="journey-card" key={cardId}>
        <div className="card-top">
          <span className="badge transfer-badge">One transfer</span>
          <strong>Score {item.score}</strong>
        </div>

        <h3>
          {route.first_train} + {route.second_train}
        </h3>

        <p className="muted">
          {route.first_train_name} → {route.second_train_name}
        </p>

        <div className="timeline">
          <div>
            <strong>{result.source}</strong>
            <span>{safeValue(route.source_departure)}</span>
          </div>

          <div>
            <strong>{route.transfer_station}</strong>
            <span>
              Wait {safeValue(route.transfer_wait_hours)} hrs ·{" "}
              {route.transfer_station_name}
            </span>
          </div>

          <div>
            <strong>{result.destination}</strong>
            <span>{safeValue(route.destination_arrival)}</span>
          </div>
        </div>

        <div className="journey-meta">
          <span>Duration {safeValue(route.total_duration_hours)} hrs</span>
          <span>{safeValue(route.total_stops)} stops</span>
          <span>Wait {safeValue(route.transfer_wait_hours)} hrs</span>
        </div>

        <button
          type="button"
          className="details-btn"
          onClick={() => toggleDetails(cardId)}
        >
          {expandedCard === cardId ? "Hide details" : "View details"}
        </button>

        {expandedCard === cardId && (
          <div className="details-panel">
            <div className="section-title">Journey breakdown</div>

            <div className="detail-grid">
              <span>First train</span>
              <strong>{route.first_train} — {route.first_train_name}</strong>

              <span>Transfer station</span>
              <strong>{route.transfer_station} — {route.transfer_station_name}</strong>

              <span>Second train</span>
              <strong>{route.second_train} — {route.second_train_name}</strong>

              <span>First leg</span>
              <strong>{safeValue(route.first_leg_duration_hours)} hrs</strong>

              <span>Wait time</span>
              <strong>{safeValue(route.transfer_wait_hours)} hrs</strong>

              <span>Second leg</span>
              <strong>{safeValue(route.second_leg_duration_hours)} hrs</strong>
            </div>
          </div>
        )}
      </div>
    );
  }

  function renderSmartRouteCard(item, index) {
    const route = item.data;
    const firstLeg = route.train_legs?.[0];

    const cardId = `smart-${index}`;

    return (
      <div className="journey-card" key={cardId}>
        <div className="card-top">
          <span className="badge direct-badge">
            {route.transfers === 0 ? "Smart direct" : "Smart route"}
          </span>
          <strong>Score {item.score}</strong>
        </div>

        <h3>{route.summary}</h3>

        <p className="muted">
          {route.route_preview?.join(" → ")}
        </p>

        <div className="journey-meta">
          <span>{route.transfers} transfers</span>
          <span>{route.leg_count} train leg{route.leg_count > 1 ? "s" : ""}</span>
          <span>{route.total_stops} stops</span>
          <span>{safeValue(route.total_duration_hours)} hrs</span>
        </div>

        {firstLeg && (
          <div className="timeline">
            <div>
              <strong>{firstLeg.from}</strong>
              <span>{safeValue(firstLeg.start_time)}</span>
            </div>

            <div>
              <strong>{firstLeg.train_no}</strong>
              <span>
                {firstLeg.train_name || "Train"} · {firstLeg.stop_count} stops
              </span>
            </div>

            <div>
              <strong>{firstLeg.to}</strong>
              <span>{safeValue(firstLeg.end_time)}</span>
            </div>
          </div>
        )}

        <button
          type="button"
          className="details-btn"
          onClick={() => toggleDetails(cardId)}
        >
          {expandedCard === cardId ? "Hide details" : "View details"}
        </button>

        {expandedCard === cardId && (
          <div className="details-panel">
            {route.reasons?.length > 0 && (
              <>
                <div className="section-title">Why recommended</div>
                <ul>
                  {route.reasons.map((reason, i) => (
                    <li key={i}>✓ {reason}</li>
                  ))}
                </ul>
              </>
            )}

            <div className="section-title">Train legs</div>
            <ul>
              {route.train_legs?.map((leg, i) => (
                <li key={i}>
                  ✓ {leg.from} → {leg.to} by {leg.train_no} ·{" "}
                  {leg.train_name || "Train"} · {safeValue(leg.start_time)} →{" "}
                  {safeValue(leg.end_time)} · {safeValue(leg.duration_hours)} hrs
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  }

  function renderRecommendation(item, index) {
    if (item.type === "direct") {
      return renderDirectCard(item, index);
    }

    if (item.type === "one_transfer") {
      return renderTransferCard(item, index);
    }

    if (item.type === "multi_transfer") {
      return renderSmartRouteCard(item, index);
    }

    return null;
  }

  return (
    <div className="page">
      <nav className="navbar">
        <div className="brand">🚆 RailYatra</div>
        <div className="nav-pill">MVP Beta</div>
      </nav>

      <main className="app">
        <header className="hero">
          <div className="pill">Smart Railway Planner</div>
          <h1>Find the best train journey</h1>
          <p>
            Search direct trains, transfer routes, duration, score and smart
            recommendations.
          </p>
        </header>

        <form className="search-card" onSubmit={searchJourney}>
          <div className="field">
            <label>From</label>
            <input
              value={source}
              onChange={(e) => {
                const value = e.target.value.toUpperCase();
                setSource(value);
                fetchStationSuggestions(value, setSourceSuggestions);
              }}
              placeholder="PNBE or Patna"
            />

            {sourceSuggestions.length > 0 && (
              <div className="suggestions-panel">
                {sourceSuggestions.map((station, index) => (
                  <button
                    type="button"
                    className="suggestion-item"
                    key={index}
                    onClick={() => {
                      setSource(getStationCode(station));
                      setSourceSuggestions([]);
                    }}
                  >
                    <strong>{getStationCode(station)}</strong>
                    <span>{getStationName(station)}</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          <button type="button" className="swap-btn" onClick={swapStations}>
            ⇅
          </button>

          <div className="field">
            <label>To</label>
            <input
              value={destination}
              onChange={(e) => {
                const value = e.target.value.toUpperCase();
                setDestination(value);
                fetchStationSuggestions(value, setDestinationSuggestions);
              }}
              placeholder="NDLS or Delhi"
            />

            {destinationSuggestions.length > 0 && (
              <div className="suggestions-panel">
                {destinationSuggestions.map((station, index) => (
                  <button
                    type="button"
                    className="suggestion-item"
                    key={index}
                    onClick={() => {
                      setDestination(getStationCode(station));
                      setDestinationSuggestions([]);
                    }}
                  >
                    <strong>{getStationCode(station)}</strong>
                    <span>{getStationName(station)}</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          <button type="submit" className="search-btn">
            {loading ? "Searching..." : "Search"}
          </button>
        </form>

        <div className="quick-routes">
          <button type="button" onClick={() => setQuickRoute("NDLS", "PNBE")}>
            NDLS → PNBE
          </button>
          <button type="button" onClick={() => setQuickRoute("PNBE", "NDLS")}>
            PNBE → NDLS
          </button>
          <button type="button" onClick={() => setQuickRoute("NDLS", "HWH")}>
            NDLS → HWH
          </button>
        </div>

        {error && <div className="error">{error}</div>}

        {loading && (
          <div className="loading">
            <div className="spinner"></div>
            Finding best journeys...
          </div>
        )}

        {result && (
          <section className="results">
            <h2>
              {result.source} → {result.destination}
            </h2>

            <p className="summary">
              Route exists: {result.route_exists ? "Yes" : "No"} · Direct:{" "}
              {result.direct_count} · One-transfer: {result.transfer_count} ·
              Smart routes: {result.multi_route_count || 0}
            </p>

            <div className="highlight-grid">
              <div className="highlight-card">
                <span>Best smart</span>
                <strong>
                  {bestSmart
                    ? bestSmart.data.summary
                    : "Not available"}
                </strong>
              </div>

              <div className="highlight-card">
                <span>Best direct</span>
                <strong>
                  {bestDirect
                    ? `${bestDirect.data.train_no} ${bestDirect.data.train_name}`
                    : "Not available"}
                </strong>
              </div>

              <div className="highlight-card">
                <span>Best transfer</span>
                <strong>
                  {bestTransfer
                    ? `${bestTransfer.data.first_train} + ${bestTransfer.data.second_train}`
                    : "Not available"}
                </strong>
              </div>

              <div className="highlight-card">
                <span>Total options</span>
                <strong>{result.total_recommendations || recommendations.length}</strong>
              </div>
            </div>

            <div className="comparison-grid">
              <div className="comparison-card">
                <span>🏆 Best overall</span>
                <strong>{getRecommendationTitle(result.best)}</strong>
                <p>{getRecommendationSubtext(result.best)}</p>
              </div>

              <div className="comparison-card">
                <span>⚡ Fastest</span>
                <strong>{getRecommendationTitle(fastestOption)}</strong>
                <p>{getRecommendationSubtext(fastestOption)}</p>
              </div>

              <div className="comparison-card">
                <span>🔁 Least transfers</span>
                <strong>{getRecommendationTitle(leastTransferOption)}</strong>
                <p>{getRecommendationSubtext(leastTransferOption)}</p>
              </div>
            </div>

            {result.best && (
              <div className="best-box">
                <span>🏆 Best recommendation</span>
                <strong>{result.best.label}</strong>
              </div>
            )}

            <div className="filter-tabs">
              <button
                type="button"
                className={activeFilter === "all" ? "active" : ""}
                onClick={() => setActiveFilter("all")}
              >
                All
              </button>

              <button
                type="button"
                className={activeFilter === "smart" ? "active" : ""}
                onClick={() => setActiveFilter("smart")}
              >
                Smart
              </button>

              <button
                type="button"
                className={activeFilter === "direct" ? "active" : ""}
                onClick={() => setActiveFilter("direct")}
              >
                Direct
              </button>

              <button
                type="button"
                className={activeFilter === "transfer" ? "active" : ""}
                onClick={() => setActiveFilter("transfer")}
              >
                Transfer
              </button>
            </div>

            <div className="sort-tabs">
              <span>Sort by</span>

              <button
                type="button"
                className={sortMode === "best" ? "active" : ""}
                onClick={() => setSortMode("best")}
              >
                Best
              </button>

              <button
                type="button"
                className={sortMode === "fastest" ? "active" : ""}
                onClick={() => setSortMode("fastest")}
              >
                Fastest
              </button>

              <button
                type="button"
                className={sortMode === "least_transfers" ? "active" : ""}
                onClick={() => setSortMode("least_transfers")}
              >
                Least Transfers
              </button>
            </div>

            {recommendations.length === 0 && (
              <div className="empty-state">No journey found for this filter.</div>
            )}

            {recommendations.map((item, index) =>
              renderRecommendation(item, index)
            )}
          </section>
        )}
      </main>
    </div>
  );
}

export default App;
