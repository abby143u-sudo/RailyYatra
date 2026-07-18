import { useEffect, useState } from "react";
import { apiUrl } from "../config/api.js";

export default function DataQualityPanel() {
  const [status, setStatus] = useState("Checking railway data quality...");
  const [quality, setQuality] = useState(null);
  const [stations, setStations] = useState([]);
  const [routes, setRoutes] = useState([]);

  useEffect(() => {
    async function loadDataQuality() {
      try {
        const [qualityResponse, stationsResponse, routesResponse] = await Promise.all([
          fetch(apiUrl("/data-quality/health")),
          fetch(apiUrl("/data-quality/stations?query=pat&limit=6")),
          fetch(apiUrl("/data-quality/demo-routes")),
        ]);
        const qualityData = await qualityResponse.json();
        const stationsData = await stationsResponse.json();
        const routesData = await routesResponse.json();
        setQuality(qualityData);
        setStations(stationsData.stations || []);
        setRoutes(routesData.routes || []);
        setStatus(qualityData.railway_data_ready ? "Railway data is ready for beta search." : "Railway data fallback is active for beta demo.");
      } catch {
        setStatus("Data-quality API unavailable. Demo routes remain available.");
      }
    }
    loadDataQuality();
  }, []);

  const counts = quality?.counts || {};

  return (
    <section className="data-quality-panel" aria-label="RailBay data quality">
      <div className="data-quality-panel__header">
        <span>Phase 17 data quality</span>
        <strong>Railway data and station autocomplete readiness</strong>
        <p>{status}</p>
      </div>

      <div className="data-quality-panel__cards">
        <article><span>Stations</span><strong>{counts.staging_stations || counts.stations || "Demo"}</strong></article>
        <article><span>Trains</span><strong>{counts.staging_trains || counts.trains || "Demo"}</strong></article>
        <article><span>Stops</span><strong>{counts.staging_train_stops || counts.train_stops || counts.stops || "Demo"}</strong></article>
        <article><span>Autocomplete</span><strong>{quality?.station_autocomplete_ready ? "Ready" : "Fallback"}</strong></article>
      </div>

      <div className="data-quality-panel__grid">
        <div>
          <strong>Station autocomplete sample</strong>
          <div className="data-quality-panel__chips">
            {stations.map((station) => <span key={station.code}>{station.code} · {station.name}</span>)}
          </div>
        </div>
        <div>
          <strong>Safe beta demo routes</strong>
          <div className="data-quality-panel__chips">
            {routes.map((route) => <span key={`${route.source}-${route.destination}`}>{route.source} → {route.destination}</span>)}
          </div>
        </div>
      </div>
    </section>
  );
}
