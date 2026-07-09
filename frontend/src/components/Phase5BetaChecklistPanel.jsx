import { useEffect, useState } from "react";
import { API_BASE } from "../config/api.js";

function displayValue(value, fallback = "—") {
  if (value === undefined || value === null || value === "") {
    return fallback;
  }

  return String(value);
}

function decisionLabel(value) {
  return value ? "Allowed" : "Blocked";
}

export default function Phase5BetaChecklistPanel() {
  const [state, setState] = useState({
    loading: true,
    error: "",
    data: null,
  });

  useEffect(() => {
    let cancelled = false;

    async function loadChecklist() {
      try {
        const response = await fetch(`${API_BASE}/product/beta-checklist`);

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        if (!cancelled) {
          setState({
            loading: false,
            error: "",
            data,
          });
        }
      } catch (error) {
        if (!cancelled) {
          setState({
            loading: false,
            error: error instanceof Error ? error.message : "Unable to reach beta checklist API",
            data: null,
          });
        }
      }
    }

    loadChecklist();

    return () => {
      cancelled = true;
    };
  }, []);

  const data = state.data;
  const readyItems = data?.ready_items || [];
  const blockedItems = data?.blocked_items || [];
  const nextActions = data?.next_actions || [];
  const decision = data?.public_beta_decision || {};
  const safety = data?.safety || {};

  return (
    <section className="phase5-beta-checklist-card">
      <div className="phase5-beta-checklist-card__header">
        <div>
          <p className="phase5-beta-checklist-card__eyebrow">Public Beta</p>
          <h2>Launch Checklist</h2>
        </div>

        <span className="phase5-beta-checklist-card__badge">/product/beta-checklist</span>
      </div>

      {state.loading && (
        <p className="phase5-beta-checklist-card__message">
          Loading public beta checklist...
        </p>
      )}

      {!state.loading && state.error && (
        <p className="phase5-beta-checklist-card__message error">
          Beta checklist API not reachable: {state.error}
        </p>
      )}

      {!state.loading && data && !state.error && (
        <>
          <div className="phase5-beta-checklist-summary">
            <div>
              <span>Status</span>
              <strong>{displayValue(data.status)}</strong>
            </div>
            <div>
              <span>Ready items</span>
              <strong>{displayValue(data.ready_count)}</strong>
            </div>
            <div>
              <span>Blocked items</span>
              <strong>{displayValue(data.blocked_count)}</strong>
            </div>
            <div>
              <span>Recommended label</span>
              <strong>{displayValue(decision.recommended_label)}</strong>
            </div>
          </div>

          <div className="phase5-beta-checklist-decision">
            <div className={decision.can_show_demo_to_users ? "allowed" : "blocked"}>
              <span>Route beta launch</span>
              <strong>
                {decisionLabel(
                  decision.can_launch_route_recommendation_public_beta ??
                    decision.can_show_demo_to_users
                )}
              </strong>
            </div>
            <div className={decision.can_show_demo_to_investors ? "allowed" : "blocked"}>
              <span>Investor demo</span>
              <strong>{decisionLabel(decision.can_show_demo_to_investors)}</strong>
            </div>
            <div className={decision.can_call_it_live_booking_product ? "allowed" : "blocked"}>
              <span>Live booking claim</span>
              <strong>{decisionLabel(decision.can_call_it_live_booking_product)}</strong>
            </div>
            <div className={decision.can_take_ticket_payments ? "allowed" : "blocked"}>
              <span>Ticket payment</span>
              <strong>{decisionLabel(decision.can_take_ticket_payments)}</strong>
            </div>
          </div>

          <div className="phase5-beta-checklist-section">
            <h3>Ready for public beta</h3>
            <div className="phase5-beta-item-list">
              {readyItems.map((item) => (
                <article className="phase5-beta-item ready" key={item.key}>
                  <div>
                    <strong>{item.label}</strong>
                    <span>{item.status}</span>
                  </div>
                  <p>{item.detail}</p>
                </article>
              ))}
            </div>
          </div>

          <div className="phase5-beta-checklist-section">
            <h3>Commercial features not included in this beta</h3>
            <div className="phase5-beta-item-list">
              {blockedItems.map((item) => (
                <article className="phase5-beta-item blocked" key={item.key}>
                  <div>
                    <strong>{item.label}</strong>
                    <span>{item.status}</span>
                  </div>
                  <p>{item.detail}</p>
                </article>
              ))}
            </div>
          </div>

          <div className="phase5-beta-checklist-section">
            <h3>Commercial roadmap</h3>
            <ol className="phase5-beta-next-actions">
              {nextActions.map((action) => (
                <li key={action}>{action}</li>
              ))}
            </ol>
          </div>

          <div className="phase5-beta-checklist-section">
            <h3>Safety confirmation</h3>
            <div className="phase5-beta-safety-grid">
              {Object.entries(safety).map(([key, value]) => (
                <div key={key}>
                  <span>{key.replaceAll("_", " ")}</span>
                  <strong>{String(value)}</strong>
                </div>
              ))}
            </div>
          </div>

          <p className="phase5-beta-checklist-card__message warning">
            GO for route-recommendation public beta. Live fares, availability, PNR, booking and payments remain unavailable.
          </p>
        </>
      )}
    </section>
  );
}
