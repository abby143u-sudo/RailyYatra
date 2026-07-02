import { useEffect, useState } from "react";
import { API_BASE } from "../config/api.js";

const STORAGE_KEY = "railyatra_demo_feedback";

export default function PublicFeedbackPanel() {
  const [feedbackType, setFeedbackType] = useState("general");
  const [message, setMessage] = useState("");
  const [savedFeedback, setSavedFeedback] = useState([]);
  const [status, setStatus] = useState("");

  useEffect(() => {
    try {
      const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
      setSavedFeedback(Array.isArray(saved) ? saved : []);
    } catch {
      setSavedFeedback([]);
    }
  }, []);

  async function syncFeedbackToBackend(entry) {
    try {
      const response = await fetch(`${API_BASE}/feedback`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(entry),
      });

      return response.ok;
    } catch {
      return false;
    }
  }

  async function saveFeedback(event) {
    event.preventDefault();

    const cleanMessage = message.trim();

    if (!cleanMessage) {
      setStatus("Please write feedback before saving.");
      return;
    }

    const entry = {
      type: feedbackType,
      message: cleanMessage,
      page: window.location.href,
      created_at: new Date().toISOString(),
    };

    const nextFeedback = [entry, ...savedFeedback].slice(0, 20);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(nextFeedback));
    setSavedFeedback(nextFeedback);
    setMessage("");

    const backendSaved = await syncFeedbackToBackend(entry);
    setStatus(backendSaved ? "Feedback saved locally and synced to backend." : "Feedback saved locally. Backend sync failed safely.");
  }

  function clearFeedback() {
    localStorage.removeItem(STORAGE_KEY);
    setSavedFeedback([]);
    setStatus("Saved feedback cleared from this browser.");
  }

  function exportFeedback() {
    const payload = JSON.stringify(savedFeedback, null, 2);

    if (!savedFeedback.length) {
      setStatus("No saved feedback to export yet.");
      return;
    }

    navigator.clipboard?.writeText(payload);
    setStatus("Feedback JSON copied to clipboard.");
  }

  return (
    <section className="public-feedback-panel" aria-label="RailYatra feedback capture">
      <div className="public-feedback-panel__intro">
        <span>Phase 10 backend feedback</span>
        <strong>Help improve the public demo</strong>
        <p>
          Capture quick feedback for bugs, route quality, UI issues and product ideas. Feedback is saved locally and also synced to the backend when available.
        </p>
      </div>

      <form className="public-feedback-panel__form" onSubmit={saveFeedback}>
        <label>
          Feedback type
          <select value={feedbackType} onChange={(event) => setFeedbackType(event.target.value)}>
            <option value="general">General</option>
            <option value="bug">Bug</option>
            <option value="route_quality">Route quality</option>
            <option value="ui">UI improvement</option>
            <option value="product_idea">Product idea</option>
          </select>
        </label>

        <label>
          Feedback
          <textarea
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            placeholder="Example: PNBE to NDLS search is clear, but route cards need simpler wording."
            rows={4}
          />
        </label>

        <div className="public-feedback-panel__actions">
          <button type="submit">Save feedback</button>
          <button type="button" onClick={exportFeedback}>Copy feedback JSON</button>
          <button type="button" onClick={clearFeedback}>Clear saved</button>
        </div>
      </form>

      {status && <p className="public-feedback-panel__status">{status}</p>}

      {savedFeedback.length > 0 && (
        <div className="public-feedback-panel__saved">
          <strong>Saved feedback in this browser: {savedFeedback.length}</strong>
          <ul>
            {savedFeedback.slice(0, 3).map((entry, index) => (
              <li key={`${entry.created_at}-${index}`}>
                <span>{entry.type}</span>
                <p>{entry.message}</p>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
