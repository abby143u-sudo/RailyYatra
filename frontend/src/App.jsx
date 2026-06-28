import { useMemo, useState } from "react";
import "./App.css";

const API_BASE = "http://127.0.0.1:8000";

function App() {
  const [source, setSource] = useState("NDLS");
  const [destination, setDestination] = useState("PNBE");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const recommendations = result?.recommendations || [];

  const bestDirect = useMemo(
    () => recommendations.find((item) => item.type === "direct"),
    [recommendations]
  );

  const bestTransfer = useMemo(
    () => recommendations.find((item) => item.type === "one_transfer"),
    [recommendations]
  );

  function cleanStation(value) {
    return value.trim().toUpperCase();
  }

  function swapStations() {
    setSource(destination);
    setDestination(source);
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

    try {
      const res = await fetch(
        `${API_BASE}/search?source=${from}&destination=${to}&limit=10`
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

  function renderDirectCard(item, index) {
    const train = item.data;

    return (
      <div className="journey-card" key={`direct-${index}`}>
        <div className="card-top">
          <span className="badge direct-badge">Direct</span>
          <strong>Score {item.score}</strong>
        </div>

        <h3>{train.train_no} — {train.train_name}</h3>

        <div className="journey-meta">
          <span>Dep {train.departure}</span>
          <span>Arr {train.arrival}</span>
          <span>{train.duration_hours} hrs</span>
          <span>{train.stops} stops</span>
        </div>

        <div className="section-title">Why recommended</div>

        <ul>
          {train.reasons?.map((reason, i) => (
            <li key={i}>✓ {reason}</li>
          ))}
        </ul>
      </div>
    );
  }

  function renderTransferCard(item, index) {
    const route = item.data;

    return (
      <div className="journey-card" key={`transfer-${index}`}>
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
            <span>{route.source_departure}</span>
          </div>

          <div>
            <strong>{route.transfer_station}</strong>
            <span>
              Wait {route.transfer_wait_hours} hrs ·{" "}
              {route.transfer_station_name}
            </span>
          </div>

          <div>
            <strong>{result.destination}</strong>
            <span>{route.destination_arrival}</span>
          </div>
        </div>

        <div className="journey-meta">
          <span>Duration {route.total_duration_hours} hrs</span>
          <span>{route.total_stops} stops</span>
          <span>Wait {route.transfer_wait_hours} hrs</span>
        </div>
      </div>
    );
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
              onChange={(e) => setSource(e.target.value.toUpperCase())}
              placeholder="NDLS"
            />
          </div>

          <button type="button" className="swap-btn" onClick={swapStations}>
            ⇅
          </button>

          <div className="field">
            <label>To</label>
            <input
              value={destination}
              onChange={(e) => setDestination(e.target.value.toUpperCase())}
              placeholder="PNBE"
            />
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
              {result.direct_count} · Transfers: {result.transfer_count}
            </p>

            <div className="highlight-grid">
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
                <strong>{recommendations.length}</strong>
              </div>
            </div>

            {result.best && (
              <div className="best-box">
                <span>🏆 Best recommendation</span>
                <strong>{result.best.label}</strong>
              </div>
            )}

            {recommendations.length === 0 && (
              <div className="empty-state">No journey found.</div>
            )}

            {recommendations.map((item, index) =>
              item.type === "direct"
                ? renderDirectCard(item, index)
                : renderTransferCard(item, index)
            )}
          </section>
        )}
      </main>
    </div>
  );
}

export default App;