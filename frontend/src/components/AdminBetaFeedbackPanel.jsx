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

  // On Vercel/live site, never use localhost even if env is wrong.
  if (!isLocalFrontend && envBase && !envBase.includes("localhost") && !envBase.includes("127.0.0.1")) {
    return envBase;
  }

  if (isLocalFrontend) {
    return envBase || LOCAL_API_BASE;
  }

  return LIVE_API_BASE;
}

export default function AdminBetaFeedbackPanel() {
  const [isOpen, setIsOpen] = useState(false);
  const [token, setToken] = useState("");
  const [feedback, setFeedback] = useState([]);
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState("");

  const apiBase = useMemo(() => getApiBase(), []);

  useEffect(() => {
    const syncHash = () => {
      setIsOpen(window.location.hash === "#admin-feedback");
    };

    syncHash();
    window.addEventListener("hashchange", syncHash);
    return () => window.removeEventListener("hashchange", syncHash);
  }, []);

  async function loadFeedback() {
    const adminToken = token.trim();

    if (!adminToken) {
      setError("Admin token paste karo.");
      setStatus("error");
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
      let data = null;

      try {
        data = text ? JSON.parse(text) : null;
      } catch {
        data = null;
      }

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
              window.location.hash = "";
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
                  <span>{item.severity || "normal"}</span>
                </div>

                <p>{item.message}</p>

                <div className="admin-feedback-meta">
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
