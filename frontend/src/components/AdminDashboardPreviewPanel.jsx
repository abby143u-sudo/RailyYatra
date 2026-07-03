import { useEffect, useMemo, useState } from "react";
import { apiUrl } from "../config/api.js";

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

async function adminGet(path, token) {
  const headers = token ? { "X-RailYatra-Admin-Token": token } : {};
  const response = await fetch(apiUrl(path), { headers });
  const data = await response.json().catch(() => ({}));
  return { response, data };
}

export default function AdminDashboardPreviewPanel() {
  const [summary, setSummary] = useState(null);
  const [auditLogs, setAuditLogs] = useState([]);
  const [authStatus, setAuthStatus] = useState(null);
  const [status, setStatus] = useState("Loading admin dashboard...");
  const [adminToken, setAdminToken] = useState(readSavedToken);
  const [needsToken, setNeedsToken] = useState(false);
  const [loading, setLoading] = useState(false);

  async function loadDashboard(token = adminToken) {
    setLoading(true);
    setStatus("Loading protected admin dashboard...");
    try {
      const auth = await adminGet("/admin/auth-status", token);
      if (auth.response.status === 401) {
        setNeedsToken(true);
        setAuthStatus(null);
        setSummary(null);
        setAuditLogs([]);
        setStatus("Admin token required. Paste the protected admin token and load again.");
        return;
      }
      if (!auth.response.ok) throw new Error("auth failed");
      setAuthStatus(auth.data);

      const demo = await adminGet("/admin/demo-summary", token);
      if (demo.response.status === 401) {
        setNeedsToken(true);
        setStatus("Admin token required for demo summary.");
        return;
      }
      if (!demo.response.ok) throw new Error("demo summary failed");
      setSummary(demo.data);

      const audit = await adminGet("/admin/audit-logs?limit=30", token);
      if (audit.response.status === 401) {
        setNeedsToken(true);
        setStatus("Admin token required for audit logs.");
        return;
      }
      if (!audit.response.ok) throw new Error("audit logs failed");
      setAuditLogs(audit.data.logs || []);
      setNeedsToken(false);
      setStatus("Protected admin dashboard loaded.");
    } catch {
      setStatus("Admin dashboard unavailable. Check backend deploy or admin token.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDashboard(readSavedToken());
  }, []);

  function handleTokenSubmit(event) {
    event.preventDefault();
    const cleanToken = adminToken.trim();
    saveToken(cleanToken);
    setAdminToken(cleanToken);
    loadDashboard(cleanToken);
  }

  function clearToken() {
    saveToken("");
    setAdminToken("");
    setNeedsToken(false);
    setSummary(null);
    setAuditLogs([]);
    setAuthStatus(null);
    setStatus("Admin token cleared from this browser session.");
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
        <span>Protected admin dashboard</span>
        <strong>Internal product health snapshot</strong>
        <p>Use the protected admin token to view feedback, analytics and audit logs. The token is stored only in this browser session.</p>
      </div>

      <form className="admin-dashboard-preview__token-form" onSubmit={handleTokenSubmit}>
        <label>
          Admin token
          <input
            type="password"
            value={adminToken}
            onChange={(event) => setAdminToken(event.target.value)}
            placeholder={needsToken ? "Token required" : "Paste protected admin token"}
            autoComplete="off"
          />
        </label>
        <button type="submit" disabled={loading}>{loading ? "Loading..." : "Load admin dashboard"}</button>
        <button type="button" onClick={clearToken}>Clear token</button>
      </form>

      <div className="admin-dashboard-preview__cards">
        <article>
          <span>Feedback items</span>
          <strong>{feedbackCount}</strong>
          <p>Stored through feedback API.</p>
        </article>
        <article>
          <span>Analytics events</span>
          <strong>{analyticsCount}</strong>
          <p>Tracked through analytics API.</p>
        </article>
        <article>
          <span>Audit logs</span>
          <strong>{auditLogs.length}</strong>
          <p>Protected admin actions.</p>
        </article>
        <article>
          <span>Admin auth</span>
          <strong>{authStatus?.admin_auth_enabled ? "Protected" : "Open preview"}</strong>
          <p>{authStatus?.auth_mode || "Waiting for auth status."}</p>
        </article>
      </div>

      <div className="admin-dashboard-preview__inbox">
        <div className="admin-dashboard-preview__section-title">
          <strong>Admin audit logs</strong>
          <span>Latest protected admin actions</span>
        </div>
        {auditLogs.length > 0 ? (
          <div className="admin-dashboard-preview__table-wrap">
            <table className="admin-dashboard-preview__table">
              <thead><tr><th>Action</th><th>Admin</th><th>Endpoint</th><th>Store</th><th>Created</th></tr></thead>
              <tbody>
                {auditLogs.map((entry, index) => (
                  <tr key={`${entry.id || entry.created_at || index}-${index}`}>
                    <td><span className="admin-dashboard-preview__pill admin-dashboard-preview__pill--audit">{entry.action || "admin_action"}</span></td>
                    <td>{entry.admin_id || "unknown_admin"}</td>
                    <td className="admin-dashboard-preview__details-cell">{entry.endpoint || "Not available"}</td>
                    <td>{entry.store || "database"}</td>
                    <td>{formatDate(entry.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="admin-dashboard-preview__empty">No audit logs loaded yet.</p>
        )}
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
          <p className="admin-dashboard-preview__empty">No feedback entries loaded yet.</p>
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
          <p className="admin-dashboard-preview__empty">No analytics events loaded yet.</p>
        )}
      </div>

      <div className="admin-dashboard-preview__details">
        <div>
          <strong>Feedback type counts</strong>
          {feedbackTypeRows.length > 0 ? <ul className="admin-dashboard-preview__mini-list">{feedbackTypeRows.map(([type, count]) => <li key={type}><span>{type}</span><strong>{count}</strong></li>)}</ul> : <p>No feedback type data loaded.</p>}
        </div>
        <div>
          <strong>Analytics type counts</strong>
          {analyticsTypeRows.length > 0 ? <ul className="admin-dashboard-preview__mini-list">{analyticsTypeRows.map(([type, count]) => <li key={type}><span>{type}</span><strong>{count}</strong></li>)}</ul> : <p>No analytics type data loaded.</p>}
        </div>
      </div>

      <p className="admin-dashboard-preview__status">{status}</p>
    </section>
  );
}
