import React, { useEffect, useMemo, useState } from "react";
import "./AdminBetaFeedbackPanel.css";

const LOCAL_API_BASE = "http://127.0.0.1:8000";
const LIVE_API_BASE = "https://railyyatra-backend.onrender.com";

function cleanBaseUrl(value) {
  return String(value || "").replace(/\/+$/, "");
}

function getApiBase() {
  const envBase = cleanBaseUrl(import.meta.env.VITE_RAILYATRA_API_BASE);
  const host = window.location.hostname;
  const isLocalFrontend = host === "localhost" || host === "127.0.0.1";

  if (isLocalFrontend) {
    return envBase || LOCAL_API_BASE;
  }

  if (envBase && !envBase.includes("localhost") && !envBase.includes("127.0.0.1")) {
    return envBase;
  }

  return LIVE_API_BASE;
}

function shouldOpenAdminPanel() {
  const hash = window.location.hash;
  const params = new URLSearchParams(window.location.search);

  return hash === "#admin-feedback" || params.get("adminFeedback") === "1";
}

const STATUS_OPTIONS = ["new", "reviewed", "resolved"];

export default function AdminBetaFeedbackPanel() {
  const [isOpen, setIsOpen] = useState(false);
  const [token, setToken] = useState("");
  const [feedback, setFeedback] = useState([]);
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState("");
  const [updatingId, setUpdatingId] = useState(null);

  const apiBase = useMemo(() => getApiBase(), []);

  useEffect(() => {
    const syncOpenState = () => {
      setIsOpen(shouldOpenAdminPanel());
    };

    syncOpenState();

    window.addEventListener("hashchange", syncOpenState);
    window.addEventListener("popstate", syncOpenState);

    return () => {
      window.removeEventListener("hashchange", syncOpenState);
      window.removeEventListener("popstate", syncOpenState);
    };
  }, []);

  async function loadFeedback() {
    const adminToken = token.trim();

    if (!adminToken) {
      setStatus("error");
      setError("Admin token paste karo.");
      return;
    }

    setStatus("loading");
    setError("");

    try {
      const response = await fetch(`${apiBase}/admin/beta-feedback`, {
        method: "GET",
        headers: {
          "X-RailYatra-Admin-Token": adminToken,
          "Content-Type": "application/json",
        },
      });

      const text = await response.text();
      const data = text ? JSON.parse(text) : null;

      if (!response.ok) {
        const message =
          data?.error?.message ||
          data?.detail ||
          text ||
          `Request failed with status ${response.status}`;

        throw new Error(message);
      }

      setFeedback(Array.isArray(data?.feedback) ? data.feedback : []);
      setStatus("success");
    } catch (err) {
      setStatus("error");
      setError(err?.message || "Could not load feedback.");
    }
  }

  async function updateFeedbackStatus(feedbackId, nextStatus) {
    const adminToken = token.trim();

    if (!adminToken) {
      setStatus("error");
      setError("Admin token paste karo.");
      return;
    }

    setUpdatingId(feedbackId);
    setError("");

    try {
      const response = await fetch(`${apiBase}/admin/beta-feedback/${feedbackId}/status`, {
        method: "PATCH",
        headers: {
          "X-RailYatra-Admin-Token": adminToken,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ status: nextStatus }),
      });

      const text = await response.text();
      const data = text ? JSON.parse(text) : null;

      if (!response.ok) {
        const message =
          data?.error?.message ||
          data?.detail ||
          text ||
          `Request failed with status ${response.status}`;

        throw new Error(message);
      }

      setFeedback((items) =>
        items.map((item) =>
          item.id === feedbackId ? { ...item, status: nextStatus } : item
        )
      );
    } catch (err) {
      setStatus("error");
      setError(err?.message || "Could not update feedback status.");
    } finally {
      setUpdatingId(null);
    }
  }

  if (!isOpen) return null;

  return (
    <div className="admin-feedback-panel">
      <div className="admin-feedback-card">
        <div className="admin-feedback-header">
          <div>
            <h2>RailYatra Beta Feedback Admin</h2>
            <p>API: {apiBase}</p>
          </div>

          <button
            type="button"
            className="admin-feedback-close"
            onClick={() => {
              window.history.pushState("", document.title, window.location.pathname);
              setIsOpen(false);
            }}
          >
            ×
          </button>
        </div>

        <div className="admin-feedback-controls">
          <input
            type="password"
            value={token}
            onChange={(event) => setToken(event.target.value)}
            placeholder="Paste admin token"
          />

          <button type="button" onClick={loadFeedback} disabled={status === "loading"}>
            {status === "loading" ? "Loading..." : "Load feedback"}
          </button>
        </div>

        {status === "error" && (
          <div className="admin-feedback-error">
            Could not load feedback: {error}
          </div>
        )}

        {status === "success" && feedback.length === 0 && (
          <div className="admin-feedback-empty">
            No feedback yet on live backend.
          </div>
        )}

        {status === "success" && feedback.length > 0 && (
          <div className="admin-feedback-list">
            {feedback.map((item) => (
              <div className="admin-feedback-item" key={item.id}>
                <div className="admin-feedback-item-top">
                  <strong>#{item.id}</strong>
                  <span className={`admin-feedback-status admin-feedback-status-${item.status || "new"}`}>
                    {item.status || "new"}
                  </span>
                </div>

                <p>{item.message}</p>

                <div className="admin-feedback-status-actions">
                  {STATUS_OPTIONS.map((option) => (
                    <button
                      type="button"
                      key={option}
                      disabled={updatingId === item.id || (item.status || "new") === option}
                      onClick={() => updateFeedbackStatus(item.id, option)}
                    >
                      {option}
                    </button>
                  ))}
                </div>

                <div className="admin-feedback-meta">
                  <span>Severity: {item.severity || "normal"}</span>
                  <span>Page: {item.page || "-"}</span>
                  <span>Route: {item.route || "-"}</span>
                  <span>Name: {item.name || "-"}</span>
                  <span>Contact: {item.contact || "-"}</span>
                  <span>{item.created_at || ""}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
