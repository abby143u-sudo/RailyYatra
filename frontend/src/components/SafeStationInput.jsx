import { useState } from "react";
import { API_BASE } from "../config/api.js";

function stationCode(station) {
  return String(station?.station_code || station?.code || station?.id || "").trim().toUpperCase();
}

function stationName(station) {
  return String(station?.station_name || station?.name || station?.label || "Station name unavailable").trim();
}

export default function SafeStationInput({ label, value, onChange, placeholder }) {
  const [stations, setStations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  async function loadStations(nextValue) {
    const query = String(nextValue || "").trim().toUpperCase();
    onChange(query);

    if (query.length < 2) {
      setStations([]);
      setLoading(false);
      setMessage("");
      return;
    }

    setLoading(true);
    setMessage("");

    try {
      const params = new URLSearchParams({ q: query, limit: "8" });
      const response = await fetch(`${API_BASE}/staging/stations?${params.toString()}`);

      if (!response.ok) {
        setStations([]);
        setMessage("");
        return;
      }

      const data = await response.json();
      const safeStations = Array.isArray(data?.stations) ? data.stations : [];
      setStations(safeStations);
      setMessage(safeStations.length ? "" : "No station found.");
    } catch {
      setStations([]);
      setMessage("");
    } finally {
      setLoading(false);
    }
  }

  function chooseStation(station) {
    const code = stationCode(station);
    onChange(code);
    setStations([]);
    setMessage("");
  }

  return (
    <div className="field safe-station-input">
      <label>{label}</label>
      <input
        value={value}
        onChange={(event) => loadStations(event.target.value)}
        onBlur={() => setTimeout(() => setStations([]), 160)}
        placeholder={placeholder}
        autoComplete="off"
      />
      {loading && <p className="safe-station-input__hint">Loading stations...</p>}
      {!loading && message && <p className="safe-station-input__hint">{message}</p>}
      {stations.length > 0 && (
        <div className="safe-station-input__panel">
          {stations.map((station, index) => {
            const code = stationCode(station);
            const name = stationName(station);
            return (
              <button
                type="button"
                key={`${code || "station"}-${index}`}
                onMouseDown={(event) => event.preventDefault()}
                onClick={() => chooseStation(station)}
              >
                <strong>{code || "N/A"}</strong>
                <span>{name}</span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
