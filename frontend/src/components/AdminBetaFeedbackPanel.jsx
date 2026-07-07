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

  if (isLocalFrontend) return envBase || LOCAL_API_BASE;

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
const FILTER_OPTIONS = ["all", "new", "reviewed", "resolved"];

export default function AdminBetaFeedbackPanel() {
  const [isOpen, setIsOpen] = useState(false);
  const [token, setToken] = useState("");
  const [feedback, setFeedback] = useState([]);
  const [loadStatus, setLoadStatus] = useState("idle");
  const [error, setError] = useState("");
  const [updatingId, setUpdatingId] = useState(null);
  const [deletingId, setDeletingId] = useState(null);
  const [statusFilter, setStatusFilter] = useState("all");
  const [searchText, setSearchText] = useState("");
  const [serverSummary, setServerSummary] = useState(null);

  const apiBase = useMemo(() => getApiBase(), []);

  const counts = useMemo(() => {
    const result = {
      all: feedback.length,
      new: 0,
      reviewed: 0,
      resolved: 0,
    };

    feedback.forEach((item) => {
      const itemStatus = item.status || "new";
      if (result[itemStatus] !== undefined) {
        result[itemStatus] += 1;
      }
    });

    return result;
  }, [feedback]);

  const filteredFeedback = useMemo(() => {
    const query = searchText.trim().toLowerCase();

    return feedback.filter((item) => {
      const itemStatus = item.status || "new";
      const matchesStatus = statusFilter === "all" || itemStatus === statusFilter;

      const searchableText = [
        item.message,
        item.page,
        item.route,
        item.severity,
        item.name,
        item.contact,
        item.created_at,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();

      const matchesSearch = !query || searchableText.includes(query);

      return matchesStatus && matchesSearch;
    });
  }, [feedback, statusFilter, searchText]);

  useEffect(() => {
    if (!isOpen || !token.trim()) {
      return undefined;
    }

    const intervalId = window.setInterval(() => {
      loadFeedback();
    }, 30000);

    return () => window.clearInterval(intervalId);
  }, [isOpen, token]);

  useEffect(() => {
    const syncOpenState = () => setIsOpen(shouldOpenAdminPanel());

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
      setLoadStatus("error");
      setError("Admin token paste karo.");
      return;
    }

    setLoadStatus("loading");
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

      const summaryResponse = await fetch(
        `${apiBase}/admin/beta-feedback/summary`,
        {
          method: "GET",
          headers: {
            "X-RailYatra-Admin-Token": adminToken,
            "Content-Type": "application/json",
          },
        }
      );

      const summaryText = await summaryResponse.text();
      const summaryData = summaryText ? JSON.parse(summaryText) : null;

      if (!summaryResponse.ok) {
        const summaryMessage =
          summaryData?.error?.message ||
          summaryData?.detail ||
          summaryText ||
          `Summary request failed with status ${summaryResponse.status}`;

        throw new Error(summaryMessage);
      }

      setServerSummary(summaryData?.counts || null);
      setLoadStatus("success");
    } catch (err) {
      setLoadStatus("error");
      setError(err?.message || "Could not load feedback.");
    }
  }

  async function updateFeedbackStatus(feedbackId, nextStatus) {
    const adminToken = token.trim();

    if (!adminToken) {
      setLoadStatus("error");
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

      const summaryResponse = await fetch(
        `${apiBase}/admin/beta-feedback/summary`,
        {
          method: "GET",
          headers: {
            "X-RailYatra-Admin-Token": adminToken,
            "Content-Type": "application/json",
          },
        }
      );

      if (summaryResponse.ok) {
        const summaryData = await summaryResponse.json();
        setServerSummary(summaryData?.counts || null);
      }

      setLoadStatus("success");
    } catch (err) {
      setLoadStatus("error");
      setError(err?.message || "Could not update feedback status.");
    } finally {
      setUpdatingId(null);
    }
  }

  async function deleteFeedback(feedbackId) {
    const adminToken = token.trim();

    if (!adminToken) {
      setLoadStatus("error");
      setError("Admin token paste karo.");
      return;
    }

    const confirmed = window.confirm(
      `Delete feedback #${feedbackId}? This cannot be undone.`
    );

    if (!confirmed) return;

    setDeletingId(feedbackId);
    setError("");

    try {
      const response = await fetch(
        `${apiBase}/admin/beta-feedback/${feedbackId}`,
        {
          method: "DELETE",
          headers: {
            "X-RailYatra-Admin-Token": adminToken,
            "Content-Type": "application/json",
          },
        }
      );

      const text = await response.text();
      const data = text ? JSON.parse(text) : null;

      if (!response.ok) {
        const message =
          data?.error?.message ||
          data?.detail ||
          text ||
          `Delete failed with status ${response.status}`;

        throw new Error(message);
      }

      setFeedback((items) =>
        items.filter((item) => item.id !== feedbackId)
      );

      setServerSummary((current) => {
        if (!current) return current;

        const deletedItem = feedback.find(
          (item) => item.id === feedbackId
        );

        const deletedStatus = deletedItem?.status || "new";

        return {
          ...current,
          total: Math.max(0, (current.total || 0) - 1),
          [deletedStatus]: Math.max(
            0,
            (current[deletedStatus] || 0) - 1
          ),
        };
      });

      setLoadStatus("success");
    } catch (err) {
      setLoadStatus("error");
      setError(err?.message || "Could not delete feedback.");
    } finally {
      setDeletingId(null);
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

          <button type="button" onClick={loadFeedback} disabled={loadStatus === "loading"}>
            {loadStatus === "loading" ? "Loading..." : "Load feedback"}
          </button>
        </div>

        {serverSummary && (
          <div className="admin-feedback-summary-grid">
            {[
              ["Total", "total"],
              ["New", "new"],
              ["Reviewed", "reviewed"],
              ["Resolved", "resolved"],
            ].map(([label, key]) => (
              <div className="admin-feedback-summary-card" key={key}>
                <span>{label}</span>
                <strong>{serverSummary[key] ?? 0}</strong>
              </div>
            ))}
          </div>
        )}

        {feedback.length > 0 && (
          <div className="admin-feedback-toolbar">
            <div className="admin-feedback-filters">
              {FILTER_OPTIONS.map((option) => (
                <button
                  type="button"
                  key={option}
                  className={statusFilter === option ? "active" : ""}
                  onClick={() => setStatusFilter(option)}
                >
                  {option} ({counts[option] || 0})
                </button>
              ))}
            </div>

            <input
              className="admin-feedback-search"
              type="search"
              value={searchText}
              onChange={(event) => setSearchText(event.target.value)}
              placeholder="Search feedback..."
            />
          </div>
        )}

        {loadStatus === "error" && (
          <div className="admin-feedback-error">
            Could not load feedback: {error}
          </div>
        )}

        {loadStatus === "success" && feedback.length === 0 && (
          <div className="admin-feedback-empty">
            No feedback yet on live backend.
          </div>
        )}

        {loadStatus === "success" && feedback.length > 0 && filteredFeedback.length === 0 && (
          <div className="admin-feedback-empty">
            No feedback matches this filter.
          </div>
        )}

        {loadStatus === "success" && filteredFeedback.length > 0 && (
          <div className="admin-feedback-list">
            {filteredFeedback.map((item) => (
              <div className="admin-feedback-item" key={item.id}>
                <div className="admin-feedback-item-top">
                  <strong>#{item.id}</strong>

                  <div className="admin-feedback-item-actions">
                    <span className={`admin-feedback-status admin-feedback-status-${item.status || "new"}`}>
                      {item.status || "new"}
                    </span>

                    <button
                      type="button"
                      className="admin-feedback-delete-button"
                      disabled={deletingId === item.id}
                      onClick={() => deleteFeedback(item.id)}
                    >
                      {deletingId === item.id ? "Deleting..." : "Delete"}
                    </button>
                  </div>
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
