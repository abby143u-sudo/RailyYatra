import React, {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import "./AdminBetaFeedbackPanel.css";

const LOCAL_API_BASE = "http://127.0.0.1:8000";
const LIVE_API_BASE = "https://api.railbay.xyz";
const PAGE_SIZE = 25;

const STATUS_OPTIONS = ["new", "reviewed", "resolved"];
const FILTER_OPTIONS = ["all", "new", "reviewed", "resolved"];

function cleanBaseUrl(value) {
  return String(value || "").replace(/\/+$/, "");
}

function getApiBase() {
  const envBase = cleanBaseUrl(
    import.meta.env.VITE_RAILYATRA_API_BASE
  );

  const host = window.location.hostname;
  const isLocal =
    host === "localhost" || host === "127.0.0.1";

  if (isLocal) {
    return envBase || LOCAL_API_BASE;
  }

  if (
    envBase &&
    !envBase.includes("localhost") &&
    !envBase.includes("127.0.0.1")
  ) {
    return envBase;
  }

  return LIVE_API_BASE;
}

function shouldOpenAdminPanel() {
  const params = new URLSearchParams(window.location.search);

  return (
    window.location.hash === "#admin-feedback" ||
    params.get("adminFeedback") === "1"
  );
}

async function readResponse(response) {
  const text = await response.text();

  if (!text) {
    return {
      text: "",
      data: null,
    };
  }

  try {
    return {
      text,
      data: JSON.parse(text),
    };
  } catch {
    return {
      text,
      data: null,
    };
  }
}

function responseError(response, result, fallback) {
  return (
    result.data?.error?.message ||
    result.data?.detail ||
    result.text ||
    fallback ||
    `Request failed with status ${response.status}`
  );
}

function csvEscape(value) {
  const safeValue = String(value ?? "");
  return `"${safeValue.replaceAll('"', '""')}"`;
}

function exportCsv(items, filename) {
  const headers = [
    "id",
    "status",
    "severity",
    "message",
    "page",
    "route",
    "name",
    "contact",
    "created_at",
  ];

  const rows = items.map((item) => [
    item.id,
    item.status || "new",
    item.severity || "normal",
    item.message || "",
    item.page || "",
    item.route || "",
    item.name || "",
    item.contact || "",
    item.created_at || "",
  ]);

  const csv = [
    headers.map(csvEscape).join(","),
    ...rows.map((row) => row.map(csvEscape).join(",")),
  ].join("\n");

  const blob = new Blob(
    [csv],
    { type: "text/csv;charset=utf-8" }
  );

  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");

  link.href = url;
  link.download = filename;

  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);

  URL.revokeObjectURL(url);
}

export default function AdminBetaFeedbackPanel() {
  const [isOpen, setIsOpen] = useState(false);
  const [token, setToken] = useState(() => {
    try {
      return sessionStorage.getItem(
        "railyatra_admin_token"
      ) || "";
    } catch {
      return "";
    }
  });
  const [feedback, setFeedback] = useState([]);
  const [loadStatus, setLoadStatus] = useState("idle");
  const [error, setError] = useState("");
  const [updatingId, setUpdatingId] = useState(null);
  const [deletingId, setDeletingId] = useState(null);
  const [statusFilter, setStatusFilter] = useState("all");
  const [searchText, setSearchText] = useState("");
  const [serverSummary, setServerSummary] = useState(null);
  const [page, setPage] = useState(1);

  const [pagination, setPagination] = useState({
    page: 1,
    pageSize: PAGE_SIZE,
    total: 0,
    totalPages: 1,
    hasPrevious: false,
    hasNext: false,
  });

  const apiBase = useMemo(() => getApiBase(), []);

  const filteredFeedback = feedback;

  const loadFeedback = useCallback(
    async (
      requestedPage = page,
      quiet = false,
      requestedStatus = statusFilter,
      requestedSearch = searchText
    ) => {
      const adminToken = token.trim();

      if (!adminToken) {
        setLoadStatus("error");
        setError("Admin token paste karo.");
        return;
      }

      if (!quiet) {
        setLoadStatus("loading");
      }

      setError("");

      try {
        const safeRequestedPage = Math.max(
          1,
          Number(requestedPage) || 1
        );

        const queryParams = new URLSearchParams({
          page: String(safeRequestedPage),
          page_size: String(PAGE_SIZE),
        });

        if (
          requestedStatus &&
          requestedStatus !== "all"
        ) {
          queryParams.set(
            "status",
            requestedStatus
          );
        }

        const normalizedSearch =
          String(requestedSearch || "").trim();

        if (normalizedSearch) {
          queryParams.set("q", normalizedSearch);
        }

        const feedbackUrl =
          `${apiBase}/admin/beta-feedback?` +
          queryParams.toString();

        const response = await fetch(feedbackUrl, {
          method: "GET",
          headers: {
            "X-RailYatra-Admin-Token": adminToken,
            "Content-Type": "application/json",
          },
        });

        const result = await readResponse(response);

        if (!response.ok) {
          throw new Error(
            responseError(
              response,
              result,
              "Could not load feedback."
            )
          );
        }

        const data = result.data || {};

        setFeedback(
          Array.isArray(data.feedback)
            ? data.feedback
            : []
        );

        const responsePage = Number(data.page) || 1;
        const totalPages = Math.max(
          1,
          Number(data.total_pages) || 1
        );

        setPage(responsePage);

        setPagination({
          page: responsePage,
          pageSize:
            Number(data.page_size) || PAGE_SIZE,
          total: Number(data.total) || 0,
          totalPages,
          hasPrevious: Boolean(data.has_previous),
          hasNext: Boolean(data.has_next),
        });

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

        const summaryResult =
          await readResponse(summaryResponse);

        if (!summaryResponse.ok) {
          throw new Error(
            responseError(
              summaryResponse,
              summaryResult,
              "Could not load summary."
            )
          );
        }

        setServerSummary(
          summaryResult.data?.counts || null
        );

        setLoadStatus("success");
      } catch (err) {
        setLoadStatus("error");
        setError(
          err?.message || "Could not load feedback."
        );
      }
    },
    [apiBase, page, searchText, statusFilter, token]
  );

  useEffect(() => {
    try {
      if (token.trim()) {
        sessionStorage.setItem(
          "railyatra_admin_token",
          token.trim()
        );
      } else {
        sessionStorage.removeItem(
          "railyatra_admin_token"
        );
      }
    } catch {
      // Session storage may be unavailable.
    }
  }, [token]);

  useEffect(() => {
    const syncOpenState = () => {
      setIsOpen(shouldOpenAdminPanel());
    };

    syncOpenState();

    window.addEventListener("hashchange", syncOpenState);
    window.addEventListener("popstate", syncOpenState);

    return () => {
      window.removeEventListener(
        "hashchange",
        syncOpenState
      );
      window.removeEventListener(
        "popstate",
        syncOpenState
      );
    };
  }, []);

  useEffect(() => {
    if (!isOpen || !token.trim()) {
      return undefined;
    }

    const intervalId = window.setInterval(() => {
      loadFeedback(page, true);
    }, 30000);

    return () => {
      window.clearInterval(intervalId);
    };
  }, [isOpen, loadFeedback, page, token]);

  async function changePage(nextPage) {
    const safePage = Math.max(
      1,
      Math.min(
        Number(nextPage) || 1,
        pagination.totalPages
      )
    );

    await loadFeedback(
      safePage,
      false,
      statusFilter,
      searchText
    );
  }

  async function updateFeedbackStatus(
    feedbackId,
    nextStatus
  ) {
    const adminToken = token.trim();

    if (!adminToken) {
      setLoadStatus("error");
      setError("Admin token paste karo.");
      return;
    }

    setUpdatingId(feedbackId);
    setError("");

    try {
      const response = await fetch(
        `${apiBase}/admin/beta-feedback/${feedbackId}/status`,
        {
          method: "PATCH",
          headers: {
            "X-RailYatra-Admin-Token": adminToken,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            status: nextStatus,
          }),
        }
      );

      const result = await readResponse(response);

      if (!response.ok) {
        throw new Error(
          responseError(
            response,
            result,
            "Could not update feedback status."
          )
        );
      }

      await loadFeedback(page, true);
    } catch (err) {
      setLoadStatus("error");
      setError(
        err?.message ||
          "Could not update feedback status."
      );
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
      `Delete feedback #${feedbackId}? ` +
        "This cannot be undone."
    );

    if (!confirmed) {
      return;
    }

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

      const result = await readResponse(response);

      if (!response.ok) {
        throw new Error(
          responseError(
            response,
            result,
            "Could not delete feedback."
          )
        );
      }

      const targetPage =
        feedback.length === 1 && page > 1
          ? page - 1
          : page;

      await loadFeedback(targetPage, true);
    } catch (err) {
      setLoadStatus("error");
      setError(
        err?.message || "Could not delete feedback."
      );
    } finally {
      setDeletingId(null);
    }
  }

  if (!isOpen) {
    return null;
  }

  return (
    <div className="admin-feedback-panel">
      <div className="admin-feedback-card">
        <div className="admin-feedback-header">
          <div>
            <h2>RailBay Beta Feedback Admin</h2>
            <p>API: {apiBase}</p>
          </div>

          <button
            type="button"
            className="admin-feedback-close"
            onClick={() => {
              window.history.pushState(
                "",
                document.title,
                window.location.pathname
              );
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
            onChange={(event) => {
              setToken(event.target.value);
              setPage(1);
            }}
            placeholder="Paste admin token"
          />

          <button
            type="button"
            disabled={loadStatus === "loading"}
            onClick={() => loadFeedback(page)}
          >
            {loadStatus === "loading"
              ? "Loading..."
              : "Load feedback"}
          </button>

          <button
            type="button"
            disabled={
              loadStatus === "loading" ||
              !token.trim()
            }
            onClick={() => loadFeedback(page)}
          >
            Refresh
          </button>

          <button
            type="button"
            className="admin-feedback-clear-token"
            disabled={!token.trim()}
            onClick={() => {
              setToken("");
              setFeedback([]);
              setServerSummary(null);
              setPage(1);
              setLoadStatus("idle");
              setError("");
            }}
          >
            Clear token
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
              <div
                className="admin-feedback-summary-card"
                key={key}
              >
                <span>{label}</span>
                <strong>
                  {serverSummary[key] ?? 0}
                </strong>
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
                  className={
                    statusFilter === option
                      ? "active"
                      : ""
                  }
                  onClick={() => {
                    setStatusFilter(option);
                    setPage(1);
                    loadFeedback(
                      1,
                      false,
                      option,
                      searchText
                    );
                  }}
                >
                  {option}
                </button>
              ))}
            </div>

            <input
              className="admin-feedback-search"
              type="search"
              value={searchText}
              onChange={(event) =>
                setSearchText(event.target.value)
              }
              placeholder="Search current page..."
            />

            <button
              type="button"
              className="admin-feedback-apply-search"
              disabled={loadStatus === "loading"}
              onClick={() => {
                setPage(1);
                loadFeedback(
                  1,
                  false,
                  statusFilter,
                  searchText
                );
              }}
            >
              Apply search
            </button>

            <div className="admin-feedback-export-actions">
              <button
                type="button"
                onClick={() =>
                  exportCsv(
                    feedback,
                    `railyatra-feedback-page-${page}.csv`
                  )
                }
              >
                Export page CSV
              </button>

              <button
                type="button"
                disabled={filteredFeedback.length === 0}
                onClick={() =>
                  exportCsv(
                    filteredFeedback,
                    `railyatra-feedback-filtered-page-${page}.csv`
                  )
                }
              >
                Export filtered CSV
              </button>
            </div>
          </div>
        )}

        {loadStatus === "error" && (
          <div className="admin-feedback-error">
            Could not load feedback: {error}
          </div>
        )}

        {loadStatus === "success" &&
          pagination.total === 0 && (
            <div className="admin-feedback-empty">
              No feedback yet on live backend.
            </div>
          )}

        {loadStatus === "success" &&
          feedback.length > 0 &&
          filteredFeedback.length === 0 && (
            <div className="admin-feedback-empty">
              No feedback matches this filter on the
              current page.
            </div>
          )}

        {loadStatus === "success" &&
          filteredFeedback.length > 0 && (
            <div className="admin-feedback-list">
              {filteredFeedback.map((item) => (
                <div
                  className="admin-feedback-item"
                  key={item.id}
                >
                  <div className="admin-feedback-item-top">
                    <strong>#{item.id}</strong>

                    <div className="admin-feedback-item-actions">
                      <span
                        className={
                          "admin-feedback-status " +
                          `admin-feedback-status-${
                            item.status || "new"
                          }`
                        }
                      >
                        {item.status || "new"}
                      </span>

                      <button
                        type="button"
                        className="admin-feedback-delete-button"
                        disabled={deletingId === item.id}
                        onClick={() =>
                          deleteFeedback(item.id)
                        }
                      >
                        {deletingId === item.id
                          ? "Deleting..."
                          : "Delete"}
                      </button>
                    </div>
                  </div>

                  <p>{item.message}</p>

                  <div className="admin-feedback-status-actions">
                    {STATUS_OPTIONS.map((option) => (
                      <button
                        type="button"
                        key={option}
                        disabled={
                          updatingId === item.id ||
                          (item.status || "new") ===
                            option
                        }
                        onClick={() =>
                          updateFeedbackStatus(
                            item.id,
                            option
                          )
                        }
                      >
                        {option}
                      </button>
                    ))}
                  </div>

                  <div className="admin-feedback-meta">
                    <span>
                      Severity:{" "}
                      {item.severity || "normal"}
                    </span>
                    <span>
                      Page: {item.page || "-"}
                    </span>
                    <span>
                      Route: {item.route || "-"}
                    </span>
                    <span>
                      Name: {item.name || "-"}
                    </span>
                    <span>
                      Contact: {item.contact || "-"}
                    </span>
                    <span>
                      {item.created_at || ""}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}

        {loadStatus === "success" &&
          pagination.total > 0 && (
            <div className="admin-feedback-pagination">
              <button
                type="button"
                disabled={!pagination.hasPrevious}
                onClick={() =>
                  changePage(page - 1)
                }
              >
                ← Previous
              </button>

              <div>
                <strong>
                  Page {pagination.page} of{" "}
                  {pagination.totalPages}
                </strong>

                <span>
                  {pagination.total} total feedback
                </span>
              </div>

              <button
                type="button"
                disabled={!pagination.hasNext}
                onClick={() =>
                  changePage(page + 1)
                }
              >
                Next →
              </button>
            </div>
          )}
      </div>
    </div>
  );
}
