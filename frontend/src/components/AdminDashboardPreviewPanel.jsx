import { useEffect, useMemo, useState } from "react";
import { API_BASE } from "../config/api.js";

const ADMIN_TOKEN_KEY = "railyatra_admin_preview_token";

function formatDate(value) {
  if (!value) return "Not available";
  try {
    return new Date(value).toLocaleString();
  } catch {
    return String(value);
  }
}

function compactJson(value) {
  if (!value || Object.keys(value).length === 0) return "No details";
  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
}

function readSavedToken() {
  try {
    return sessionStorage.getItem(ADMIN_TOKEN_KEY) || "";
  } catch {
    return "";
  }
}

function saveToken(value) {
  try {
    if (value) {
      sessionStorage.setItem(ADMIN_TOKEN_KEY, value);
    } else {
      sessionStorage.removeItem(ADMIN_TOKEN_KEY);
    }
  } catch {
    return;
  }
}

export default function AdminDashboardPreviewPanel() {
  const [summary, setSummary] = useState(null);
  const [status, setStatus] = useState("Loading admin summary...");
  const [adminToken, setAdminToken] = useState(readSavedToken);
  const [needsToken, setNeedsToken] = useState(false);

  async function loadSummary(token = adminToken) {
    setStatus("Loading admin summary...");
    try {
      const headers = token ? { "X-RailYatra-Admin-Token": token } : {};
      const response = await fetch(`${API_BASE}/admin/demo-summary`, { headers });

      if (response.status === 401) {
        setNeedsToken(true);
        setSummary(null);
        setStatus("Admin token required. Enter the token to load the protected dashboard.");
        return;
      }

      if (!response.ok) {
        throw new Error(`Admin summary failed with ${response.status}`);
      }

      const data = await response.json();
      setSummary(data);
      setNeedsToken(false);
      setStatus(token ? "Admin summary loaded with token." : "Admin summary loaded from backend.");
    } catch {
      setSummary(null);
      setStatus("Admin summary unavailable. Check backend deploy, admin token, or API connection.");
    }
  }

  useEffect(() => {
    loadSummary(readSavedToken());
  }, []);

  function handleTokenSubmit(event) {
    event.preventDefault();
    const cleanToken = adminToken.trim();
    saveToken(cleanToken);
    setAdminToken(cleanToken);
    loadSummary(cleanToken);
  }

  function clearToken() {
    saveToken("");
    setAdminToken("");
    setNeedsToken(false);
    loadSummary("");
  }

  const feedbackCount = summary?.feedback?.count ?? 0;
  const analyticsCount = summary?.analytics?.count ?? 0;
  const latestFeedback = summary?.feedback?.latest || [];
  const latestAnalytics = summary?.analytics?.latest || [];
  const feedbackTypes = summary?.feedback?.by_type || {};
  const analyticsTypes = summary?.analytics?.by_type || {};

  const feedbackTypeRows = useMemo(() => Object.entries(feedbackTypes), [feedbackTypes]);
  const analyticsTypeRows = useMemo(() => Object.entries(analyticsTypes), [analyticsTypes]);

  return (
    <section className="admin-dashboard-preview" aria-label="RailYatra admin dashboard preview">
      <div className="admin-dashboard-preview__header">
        <span>Phase 11 admin dashboard preview</span>
        <strong>Internal product health snapshot</strong>
        <p>This preview reads backend admin summaries for feedback and analytics. When admin token protection is enabled, enter the token locally in this browser session.</p>
      </div>

      <form className="admin-dashboard-preview__token-form" onSubmit={handleTokenSubmit}>
        <label>
          Admin token
          <input
            type="password"
            value={adminToken}
            onChange={(event) => setAdminToken(event.target.value)}
            placeholder={needsToken ? "Token required" : "Optional unless protected on backend"}
            autoComplete="off"
          />
        </label>
        <button type="submit">Load admin summary</button>
        <button type="button" onClick={clearToken}>Clear token</button>
      </form>

      <div className="admin-dashboard-preview__cards">
        <article>
          <span>Feedback items</span>
          <strong>{feedbackCount}</strong>
          <p>Stored through the feedback API.</p>
        </article>
        <article>
          <span>Analytics events</span>
          <strong>{analyticsCount}</strong>
          <p>Tracked through the analytics API.</p>
        </article>
        <article>
          <span>Booking enabled</span>
          <strong>{summary?.live_feature_boundary?.booking ? "Yes" : "No"}</strong>
          <p>Product boundary remains visible.</p>
        </article>
      </div>

      <div className="admin-dashboard-preview__inbox">
        <div className="admin-dashboard-preview__section-title">
          <strong>Feedback inbox</strong>
          <span>Latest public demo feedback</span>
        </div>
        {latestFeedback.length > 0 ? (
          <div className="admin-dashboard-preview__table-wrap">
            <table className="admin-dashboard-preview__table">
              <thead><tr><th>Type</th><th>Message</th><th>Created</th><th>Source</th></tr></thead>
              <tbody>
                {latestFeedback.map((entry, index) => (
                  <tr key={`${entry.id || entry.server_created_at || index}-${index}`}>
                    <td><span className="admin-dashboard-preview__pill">{entry.type || "general"}</span></td>
                    <td>{entry.message || "No message"}</td>
                    <td>{formatDate(entry.server_created_at || entry.client_created_at)}</td>
                    <td>{entry.source || "public_demo"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="admin-dashboard-preview__empty">No feedback entries yet.</p>
        )}
      </div>

      <div className="admin-dashboard-preview__inbox admin-dashboard-preview__analytics-table">
        <div className="admin-dashboard-preview__section-title">
          <strong>Analytics event table</strong>
          <span>Latest tracked demo events</span>
        </div>
        {latestAnalytics.length > 0 ? (
          <div className="admin-dashboard-preview__table-wrap">
            <table className="admin-dashboard-preview__table">
              <thead><tr><th>Event</th><th>Details</th><th>Created</th><th>Page</th></tr></thead>
              <tbody>
                {latestAnalytics.map((entry, index) => (
                  <tr key={`${entry.id || entry.server_created_at || index}-${index}`}>
                    <td><span className="admin-dashboard-preview__pill admin-dashboard-preview__pill--analytics">{entry.type || "custom_event"}</span></td>
                    <td className="admin-dashboard-preview__details-cell">{compactJson(entry.details || {})}</td>
                    <td>{formatDate(entry.server_created_at || entry.client_created_at)}</td>
                    <td>{entry.page || "Not available"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="admin-dashboard-preview__empty">No analytics events yet.</p>
        )}
      </div>

      <div className="admin-dashboard-preview__details">
        <div>
          <strong>Feedback type counts</strong>
          {feedbackTypeRows.length > 0 ? <ul className="admin-dashboard-preview__mini-list">{feedbackTypeRows.map(([type, count]) => <li key={type}><span>{type}</span><strong>{count}</strong></li>)}</ul> : <p>No feedback type data yet.</p>}
        </div>
        <div>
          <strong>Analytics type counts</strong>
          {analyticsTypeRows.length > 0 ? <ul className="admin-dashboard-preview__mini-list">{analyticsTypeRows.map(([type, count]) => <li key={type}><span>{type}</span><strong>{count}</strong></li>)}</ul> : <p>No analytics type data yet.</p>}
        </div>
      </div>

      <p className="admin-dashboard-preview__status">{status}</p>
    </section>
  );
}
