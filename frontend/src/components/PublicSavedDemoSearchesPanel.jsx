import { useEffect, useState } from "react";

const STORAGE_KEY = "railyatra_saved_demo_searches";

const DEFAULT_ROUTES = [
  {
    source: "DSNR",
    destination: "TPKR",
    label: "Best public demo route",
    note: "Use this first during a demo.",
  },
  {
    source: "PNBE",
    destination: "NDLS",
    label: "Patna to Delhi test",
    note: "Good familiar route for manual QA.",
  },
  {
    source: "LTT",
    destination: "VVH",
    label: "Recommendation smoke route",
    note: "Used in deployed smoke testing.",
  },
];

function normalizeCode(value) {
  return String(value || "").trim().toUpperCase();
}

function readSavedRoutes() {
  try {
    const parsed = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function saveRoutes(routes) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(routes.slice(0, 12)));
}

export default function PublicSavedDemoSearchesPanel({
  currentSource,
  currentDestination,
  onApplyRoute,
}) {
  const [savedRoutes, setSavedRoutes] = useState([]);
  const [status, setStatus] = useState("");

  useEffect(() => {
    setSavedRoutes(readSavedRoutes());
  }, []);

  function applyRoute(source, destination) {
    onApplyRoute?.(source, destination);
    setStatus(`Applied ${source} → ${destination}. Now press Search routes.`);
  }

  function saveCurrentRoute() {
    const source = normalizeCode(currentSource);
    const destination = normalizeCode(currentDestination);

    if (!source || !destination) {
      setStatus("Enter both From and To station codes before saving.");
      return;
    }

    if (source === destination) {
      setStatus("Source and destination must be different.");
      return;
    }

    const route = {
      source,
      destination,
      label: "Saved demo route",
      note: "Saved from current main search.",
      created_at: new Date().toISOString(),
    };

    const nextRoutes = [
      route,
      ...savedRoutes.filter(
        (item) => !(item.source === source && item.destination === destination),
      ),
    ].slice(0, 12);

    saveRoutes(nextRoutes);
    setSavedRoutes(nextRoutes);
    setStatus(`Saved ${source} → ${destination}.`);
  }

  function clearSavedRoutes() {
    localStorage.removeItem(STORAGE_KEY);
    setSavedRoutes([]);
    setStatus("Saved demo routes cleared.");
  }

  const allRoutes = [...DEFAULT_ROUTES, ...savedRoutes];

  return (
    <section className="public-saved-demo-searches" aria-label="RailYatra saved demo searches">
      <div className="public-saved-demo-searches__intro">
        <span>Phase 9 saved searches</span>
        <strong>Quick demo routes</strong>
        <p>
          Use ready-made route examples during demos, or save your current From/To route in this browser.
        </p>
      </div>

      <div className="public-saved-demo-searches__actions">
        <button type="button" onClick={saveCurrentRoute}>
          Save current route
        </button>
        <button type="button" onClick={clearSavedRoutes}>
          Clear saved routes
        </button>
      </div>

      {status && <p className="public-saved-demo-searches__status">{status}</p>}

      <div className="public-saved-demo-searches__grid">
        {allRoutes.map((route, index) => (
          <article key={`${route.source}-${route.destination}-${index}`}>
            <span>{route.label}</span>
            <strong>{route.source} → {route.destination}</strong>
            <p>{route.note}</p>
            <button
              type="button"
              onClick={() => applyRoute(route.source, route.destination)}
            >
              Use this route
            </button>
          </article>
        ))}
      </div>
    </section>
  );
}
