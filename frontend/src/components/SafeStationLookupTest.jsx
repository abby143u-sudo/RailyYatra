import { useState } from "react";
import { API_BASE } from "../config/api.js";

function getStationCode(station) {
  return String(station?.station_code || station?.code || station?.id || "").trim().toUpperCase();
}

function getStationName(station) {
  return String(station?.station_name || station?.name || station?.label || "Station name unavailable").trim();
}

export default function SafeStationLookupTest() {
  const [query, setQuery] = useState("");
  const [stations, setStations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("Type at least 2 letters to test station lookup safely.");

  async function loadStations(value) {
    const nextQuery = String(value || "").trim().toUpperCase();
    setQuery(nextQuery);

    if (nextQuery.length < 2) {
      setStations([]);
      setLoading(false);
      setMessage("Type at least 2 letters to test station lookup safely.");
      return;
    }

    setLoading(true);
    setMessage("");

    try {
      const params = new URLSearchParams({ q: nextQuery, limit: "8" });
      const response = await fetch(`${API_BASE}/staging/stations?${params.toString()}`);

      if (!response.ok) {
        setStations([]);
        setMessage(`Station lookup returned HTTP ${response.status}.`);
        return;
      }

      const data = await response.json();
      const safeStations = Array.isArray(data?.stations) ? data.stations : [];
      setStations(safeStations);
      setMessage(safeStations.length ? "" : "No stations found for this query.");
    } catch {
      setStations([]);
      setMessage("Station lookup failed safely. Page did not crash.");
    } finally {
      setLoading(false);
    }
  }

  function chooseStation(station) {
    const code = getStationCode(station);
    setQuery(code);
    setStations([]);
    setMessage(code ? `Selected ${code}. Safe lookup test passed.` : "Selected station has no code.");
  }

  return (
    <section className="safe-station-lookup-test" aria-label="Safe station lookup test">
      <div className="safe-station-lookup-test__header">
        <span>Safe autocomplete test</span>
        <strong>Station lookup is isolated from the main search</strong>
        <p>
          Type PNBE, NDLS, LTT, DSNR or any station query here. This test should never blank the page.
        </p>
      </div>

      <label className="safe-station-lookup-test__field">
        <span>Station lookup</span>
        <input
          value={query}
          onChange={(event) => loadStations(event.target.value)}
          placeholder="Try PNBE or NDLS"
          autoComplete="off"
        />
      </label>

      {loading && <p className="safe-station-lookup-test__message">Loading stations...</p>}
      {!loading && message && <p className="safe-station-lookup-test__message">{message}</p>}

      {stations.length > 0 && (
        <div className="safe-station-lookup-test__results">
          {stations.map((station, index) => {
            const code = getStationCode(station);
            const name = getStationName(station);
            return (
              <button
                type="button"
                key={`${code || "station"}-${index}`}
                onClick={() => chooseStation(station)}
              >
                <strong>{code || "N/A"}</strong>
                <span>{name}</span>
              </button>
            );
          })}
        </div>
      )}
    </section>
  );
}
