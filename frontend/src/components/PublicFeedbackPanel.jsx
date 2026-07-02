import { useEffect, useState } from "react";

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

  function saveFeedback(event) {
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
    setStatus("Feedback saved locally for this demo browser.");
  }

  function clearFeedback() {
    localStorage.removeItem(STORAGE_KEY);
    setSavedFeedback([]);
    setStatus("Saved feedback cleared.");
  }

  return (
    <section className="public-feedback-panel" aria-label="RailYatra feedback capture">
      <div className="public-feedback-panel__intro">
        <span>Phase 9 feedback capture</span>
        <strong>Help improve the public demo</strong>
        <p>
          Capture quick feedback for bugs, route quality, UI issues and product ideas. This is stored locally in the browser for now.
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
