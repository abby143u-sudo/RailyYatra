import { useEffect, useMemo, useState } from "react";
import { API_BASE } from "../config/api.js";

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

export default function AdminDashboardPreviewPanel() {
  const [summary, setSummary] = useState(null);
  const [status, setStatus] = useState("Loading admin summary...");

  useEffect(() => {
    let active = true;

    async function loadSummary() {
      try {
        const response = await fetch(`${API_BASE}/admin/demo-summary`);
        if (!response.ok) {
          throw new Error(`Admin summary failed with ${response.status}`);
        }
        const data = await response.json();
        if (!active) return;
        setSummary(data);
        setStatus("Admin summary loaded from backend.");
      } catch {
        if (!active) return;
        setSummary(null);
        setStatus("Admin summary unavailable. If admin token is enabled, this panel should move behind protected login.");
      }
    }

    loadSummary();
    return () => {
      active = false;
    };
  }, []);

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
        <p>This preview reads backend admin summaries for feedback and analytics. In production, this screen should be protected by admin login.</p>
      </div>

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
              <thead>
                <tr>
                  <th>Type</th>
                  <th>Message</th>
                  <th>Created</th>
                  <th>Source</th>
                </tr>
              </thead>
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
          <p className="admin-dashboard-preview__empty">No feedback entries yet. Submit feedback from the public demo to populate this inbox.</p>
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
              <thead>
                <tr>
                  <th>Event</th>
                  <th>Details</th>
                  <th>Created</th>
                  <th>Page</th>
                </tr>
              </thead>
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
          <p className="admin-dashboard-preview__empty">No analytics events yet. Open the public demo and submit a search to populate this table.</p>
        )}
      </div>

      <div className="admin-dashboard-preview__details">
        <div>
          <strong>Feedback type counts</strong>
          {feedbackTypeRows.length > 0 ? (
            <ul className="admin-dashboard-preview__mini-list">
              {feedbackTypeRows.map(([type, count]) => (
                <li key={type}><span>{type}</span><strong>{count}</strong></li>
              ))}
            </ul>
          ) : (
            <p>No feedback type data yet.</p>
          )}
        </div>
        <div>
          <strong>Analytics type counts</strong>
          {analyticsTypeRows.length > 0 ? (
            <ul className="admin-dashboard-preview__mini-list">
              {analyticsTypeRows.map(([type, count]) => (
                <li key={type}><span>{type}</span><strong>{count}</strong></li>
              ))}
            </ul>
          ) : (
            <p>No analytics type data yet.</p>
          )}
        </div>
      </div>

      <p className="admin-dashboard-preview__status">{status}</p>
    </section>
  );
}
