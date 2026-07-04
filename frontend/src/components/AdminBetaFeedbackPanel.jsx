import { useEffect, useState } from "react";
import "./AdminBetaFeedbackPanel.css";

const fallbackApiBase = "http://127.0.0.1:8000";
const API_BASE = import.meta.env.VITE_RAILYATRA_API_BASE || fallbackApiBase;

function AdminBetaFeedbackPanel() {
  const [visible, setVisible] = useState(window.location.hash === "#admin-feedback");
  const [token, setToken] = useState(localStorage.getItem("railyatra_admin_token") || "");
  const [feedback, setFeedback] = useState([]);
  const [status, setStatus] = useState("");

  useEffect(() => {
    const onHashChange = () => {
      setVisible(window.location.hash === "#admin-feedback");
    };

    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  async function loadFeedback() {
    setStatus("Loading feedback...");

    try {
      localStorage.setItem("railyatra_admin_token", token);

      const response = await fetch(`${API_BASE}/admin/beta-feedback`, {
        headers: token ? { "x-admin-token": token } : {},
      });

      const data = await response.json();

      if (!response.ok || !data.ok) {
        throw new Error(data.detail || "Could not load feedback.");
      }

      setFeedback(data.feedback || []);
      setStatus(`Loaded ${data.count || 0} feedback items.`);
    } catch (error) {
      setStatus(error.message || "Feedback load failed.");
    }
  }

  if (!visible) {
    return null;
  }

  return (
    <div className="admin-feedback-page">
      <div className="admin-feedback-card">
        <div className="admin-feedback-header">
          <div>
            <p className="admin-feedback-kicker">RailYatra Admin</p>
            <h2>Beta Feedback</h2>
            <p>Review public beta issues, route problems, and user suggestions.</p>
          </div>

          <button
            type="button"
            onClick={() => {
              window.location.hash = "";
              setVisible(false);
            }}
          >
            Close
          </button>
        </div>

        <div className="admin-feedback-controls">
          <input
            value={token}
            onChange={(event) => setToken(event.target.value)}
            placeholder="Admin token optional for local dev"
          />

          <button type="button" onClick={loadFeedback}>
            Load feedback
          </button>
        </div>

        {status && <p className="admin-feedback-status">{status}</p>}

        <div className="admin-feedback-list">
          {feedback.length === 0 ? (
            <p className="admin-feedback-empty">No feedback loaded yet.</p>
          ) : (
            feedback.map((item) => (
              <div className="admin-feedback-item" key={item.id}>
                <div className="admin-feedback-item-top">
                  <strong>#{item.id} · {item.severity || "normal"}</strong>
                  <span>{item.created_at || "time unavailable"}</span>
                </div>

                <p>{item.message}</p>

                <div className="admin-feedback-meta">
                  <span>Page: {item.page || "—"}</span>
                  <span>Route: {item.route || "—"}</span>
                  <span>Contact: {item.contact || "—"}</span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

export default AdminBetaFeedbackPanel;
