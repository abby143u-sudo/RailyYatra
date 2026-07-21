import { useState } from "react";
import "./BetaFeedbackWidget.css";
import { API_BASE } from "../config/api.js";

function BetaFeedbackWidget() {
  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [contact, setContact] = useState("");
  const [severity, setSeverity] = useState("normal");
  const [status, setStatus] = useState("");

  async function submitFeedback(event) {
    event.preventDefault();

    const trimmed = message.trim();

    if (trimmed.length < 3) {
      setStatus("Please write at least 3 characters.");
      return;
    }

    setStatus("Sending...");

    try {
      const response = await fetch(`${API_BASE}/beta/feedback`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: trimmed,
          contact: contact.trim(),
          severity,
          page: window.location.href,
          route: "public-beta",
        }),
      });

      const data = await response.json();

      if (!response.ok || !data.ok) {
        throw new Error(data.detail || "Feedback failed");
      }

      setStatus("Feedback sent. Thank you!");
      setMessage("");
      setContact("");

      setTimeout(() => {
        setOpen(false);
        setStatus("");
      }, 1200);
    } catch (error) {
      setStatus(error.message || "Could not send feedback.");
    }
  }

  return (
    <div className="beta-feedback-widget">
      {open && (
        <form className="beta-feedback-panel" onSubmit={submitFeedback}>
          <div className="beta-feedback-header">
            <strong>RailBay Beta Feedback</strong>
            <button type="button" onClick={() => setOpen(false)} aria-label="Close feedback">
              ×
            </button>
          </div>

          <label>
            Issue type
            <select value={severity} onChange={(event) => setSeverity(event.target.value)}>
              <option value="normal">Feedback</option>
              <option value="bug">Bug</option>
              <option value="route_issue">Route issue</option>
              <option value="data_issue">Data issue</option>
              <option value="urgent">Urgent</option>
            </select>
          </label>

          <label>
            Message
            <textarea
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              placeholder="Tell us what went wrong or what should improve..."
              rows={4}
            />
          </label>

          <label>
            Contact optional
            <input
              value={contact}
              onChange={(event) => setContact(event.target.value)}
              placeholder="Email or phone optional"
            />
          </label>

          <button className="beta-feedback-submit" type="submit">
            Send feedback
          </button>

          {status && <p className="beta-feedback-status">{status}</p>}
        </form>
      )}

      <button className="beta-feedback-button" type="button" onClick={() => setOpen(true)}>
        Feedback
      </button>
    </div>
  );
}

export default BetaFeedbackWidget;
