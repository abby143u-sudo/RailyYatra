import { useEffect, useState } from "react";
import { API_BASE } from "../config/api.js";

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
  const feedbackTypes = summary?.feedback?.by_type || {};
  const analyticsTypes = summary?.analytics?.by_type || {};

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

      <div className="admin-dashboard-preview__details">
        <div>
          <strong>Feedback types</strong>
          <pre>{JSON.stringify(feedbackTypes, null, 2)}</pre>
        </div>
        <div>
          <strong>Analytics types</strong>
          <pre>{JSON.stringify(analyticsTypes, null, 2)}</pre>
        </div>
      </div>

      <p className="admin-dashboard-preview__status">{status}</p>
    </section>
  );
}
