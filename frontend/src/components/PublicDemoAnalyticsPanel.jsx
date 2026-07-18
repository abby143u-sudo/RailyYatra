import { useEffect, useMemo, useState } from "react";

const STORAGE_KEY = "railyatra_demo_analytics";

function readEvents() {
  try {
    const parsed = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function saveEvents(events) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(events.slice(0, 100)));
}

function trackEvent(type, details = {}) {
  const entry = {
    type,
    details,
    created_at: new Date().toISOString(),
    page: window.location.href,
  };

  const nextEvents = [entry, ...readEvents()].slice(0, 100);
  saveEvents(nextEvents);
  window.dispatchEvent(new CustomEvent("railyatra-demo-analytics-updated"));
}

function readMainSearchSnapshot(form) {
  const inputs = Array.from(form.querySelectorAll("input, select"));
  const values = inputs.map((input) => input.value).filter(Boolean);

  return {
    source: values[0] || "",
    destination: values[1] || "",
    train_type: values[2] || "",
    class_code: values[3] || "",
    quota: values[4] || "",
    journey_date: values[5] || "",
  };
}

export default function PublicDemoAnalyticsPanel() {
  const [events, setEvents] = useState([]);

  useEffect(() => {
    const existingEvents = readEvents();
    setEvents(existingEvents);

    trackEvent("page_view", {
      path: window.location.pathname,
      title: document.title,
    });

    const refreshEvents = () => setEvents(readEvents());
    window.addEventListener("railyatra-demo-analytics-updated", refreshEvents);

    const mainSearchForm = document.getElementById("main-search");

    function handleMainSearchSubmit() {
      if (!mainSearchForm) return;

      trackEvent("main_search_submit", readMainSearchSnapshot(mainSearchForm));
    }

    if (mainSearchForm) {
      mainSearchForm.addEventListener("submit", handleMainSearchSubmit, true);
    }

    return () => {
      window.removeEventListener("railyatra-demo-analytics-updated", refreshEvents);

      if (mainSearchForm) {
        mainSearchForm.removeEventListener("submit", handleMainSearchSubmit, true);
      }
    };
  }, []);

  const summary = useMemo(() => {
    return events.reduce(
      (acc, event) => {
        acc.total += 1;
        acc.byType[event.type] = (acc.byType[event.type] || 0) + 1;
        return acc;
      },
      { total: 0, byType: {} },
    );
  }, [events]);

  function clearAnalytics() {
    localStorage.removeItem(STORAGE_KEY);
    setEvents([]);
    window.dispatchEvent(new CustomEvent("railyatra-demo-analytics-updated"));
  }

  function exportAnalytics() {
    const payload = JSON.stringify(events, null, 2);
    navigator.clipboard?.writeText(payload);
  }

  return (
    <section className="public-demo-analytics-panel" aria-label="RailBay demo analytics">
      <div className="public-demo-analytics-panel__intro">
        <span>Phase 9 analytics</span>
        <strong>Local demo event tracking</strong>
        <p>
          Tracks demo page views and main search submissions in this browser only. This helps validate demo usage before adding production analytics.
        </p>
      </div>

      <div className="public-demo-analytics-panel__stats">
        <article>
          <span>Total events</span>
          <strong>{summary.total}</strong>
        </article>
        <article>
          <span>Page views</span>
          <strong>{summary.byType.page_view || 0}</strong>
        </article>
        <article>
          <span>Search submits</span>
          <strong>{summary.byType.main_search_submit || 0}</strong>
        </article>
      </div>

      <div className="public-demo-analytics-panel__actions">
        <button type="button" onClick={exportAnalytics}>
          Copy analytics JSON
        </button>
        <button type="button" onClick={clearAnalytics}>
          Clear analytics
        </button>
      </div>

      {events.length > 0 && (
        <div className="public-demo-analytics-panel__recent">
          <strong>Recent demo events</strong>
          <ul>
            {events.slice(0, 4).map((event, index) => (
              <li key={`${event.created_at}-${index}`}>
                <span>{event.type}</span>
                <p>{new Date(event.created_at).toLocaleString()}</p>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
