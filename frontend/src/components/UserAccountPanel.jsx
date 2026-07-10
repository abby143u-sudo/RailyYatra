import { useEffect, useState } from "react";
import { apiUrl } from "../config/api.js";
import "./UserAccountPanel.css";


const LOCAL_SAVED_ROUTES_KEY =
  "railyatra_saved_demo_searches";


const EMPTY_SECURITY_FORM = {
  current_password: "",
  new_password: "",
  delete_password: "",
  delete_confirmation: "",
};


function normalizeCode(value) {
  return String(value || "")
    .trim()
    .toUpperCase();
}


function readErrorMessage(payload, fallback) {
  return (
    payload?.error?.message ||
    payload?.detail ||
    payload?.message ||
    fallback
  );
}


async function accountRequest(
  path,
  options = {},
) {
  const hasBody =
    options.body !== undefined &&
    options.body !== null;

  const response = await fetch(
    apiUrl(path),
    {
      ...options,
      credentials: "include",
      headers: {
        Accept: "application/json",
        ...(hasBody
          ? {
              "Content-Type":
                "application/json",
            }
          : {}),
        ...(options.headers || {}),
      },
    },
  );

  const payload = await response
    .json()
    .catch(() => null);

  if (!response.ok) {
    const error = new Error(
      readErrorMessage(
        payload,
        `Request failed with HTTP ${response.status}.`,
      ),
    );

    error.status = response.status;
    throw error;
  }

  return payload;
}


function readBrowserSavedRoutes() {
  try {
    const parsed = JSON.parse(
      localStorage.getItem(
        LOCAL_SAVED_ROUTES_KEY,
      ) || "[]",
    );

    if (!Array.isArray(parsed)) {
      return [];
    }

    return parsed
      .map((route) => ({
        source: normalizeCode(route.source),
        destination: normalizeCode(
          route.destination,
        ),
        journey_date:
          String(
            route.journey_date || "",
          ).trim(),
        class_code: normalizeCode(
          route.class_code || "SL",
        ),
        quota: normalizeCode(
          route.quota || "GN",
        ),
        label: String(
          route.label ||
            "Imported browser journey",
        ).slice(0, 120),
        note: String(
          route.note ||
            "Imported from this browser.",
        ).slice(0, 500),
      }))
      .filter(
        (route) =>
          route.source &&
          route.destination &&
          route.source !== route.destination,
      )
      .slice(0, 50);
  } catch {
    return [];
  }
}


export default function UserAccountPanel({
  currentSource,
  currentDestination,
  currentJourneyDate,
  currentClassCode,
  currentQuota,
  onApplyRoute,
}) {
  const [sessionState, setSessionState] =
    useState("checking");
  const [user, setUser] = useState(null);
  const [journeys, setJourneys] =
    useState([]);
  const [mode, setMode] = useState("login");
  const [busy, setBusy] = useState("");
  const [message, setMessage] =
    useState("");
  const [form, setForm] = useState({
    display_name: "",
    email: "",
    password: "",
  });
  const [securityForm, setSecurityForm] =
    useState({
      ...EMPTY_SECURITY_FORM,
    });

  useEffect(() => {
    let cancelled = false;

    async function bootstrapAccount() {
      try {
        const sessionPayload =
          await accountRequest("/auth/me");

        if (cancelled) {
          return;
        }

        setUser(sessionPayload.user);
        setSessionState("authenticated");

        const journeyPayload =
          await accountRequest(
            "/account/saved-journeys",
          );

        if (!cancelled) {
          setJourneys(
            journeyPayload.journeys || [],
          );
        }
      } catch (error) {
        if (cancelled) {
          return;
        }

        setUser(null);
        setJourneys([]);
        setSessionState("guest");

        if (error.status !== 401) {
          setMessage(
            "Account service is temporarily unavailable.",
          );
        }
      }
    }

    bootstrapAccount();

    return () => {
      cancelled = true;
    };
  }, []);

  async function refreshJourneys() {
    const payload = await accountRequest(
      "/account/saved-journeys",
    );

    setJourneys(payload.journeys || []);
  }

  function updateForm(field, value) {
    setForm((current) => ({
      ...current,
      [field]: value,
    }));
  }


  function updateSecurityForm(field, value) {
    setSecurityForm((current) => ({
      ...current,
      [field]: value,
    }));
  }

  async function submitAuthentication(
    event,
  ) {
    event.preventDefault();
    setBusy("authentication");
    setMessage("");

    try {
      const isRegister = mode === "register";

      const body = isRegister
        ? {
            display_name:
              form.display_name,
            email: form.email,
            password: form.password,
          }
        : {
            email: form.email,
            password: form.password,
          };

      const payload = await accountRequest(
        isRegister
          ? "/auth/register"
          : "/auth/login",
        {
          method: "POST",
          body: JSON.stringify(body),
        },
      );

      setUser(payload.user);
      setSessionState("authenticated");
      setForm((current) => ({
        ...current,
        password: "",
      }));

      await refreshJourneys();

      setMessage(
        isRegister
          ? "Account created successfully."
          : "Login successful.",
      );
    } catch (error) {
      setMessage(error.message);
    } finally {
      setBusy("");
    }
  }

  async function logout() {
    setBusy("logout");
    setMessage("");

    try {
      await accountRequest(
        "/auth/logout",
        {
          method: "POST",
        },
      );
    } catch {
      // Clear the frontend session even when
      // the backend logout response is unavailable.
    } finally {
      setUser(null);
      setJourneys([]);
      setSessionState("guest");
      setSecurityForm({
        ...EMPTY_SECURITY_FORM,
      });
      setBusy("");
      setMessage("You have been logged out.");
    }
  }

  async function changePassword(event) {
    event.preventDefault();
    setBusy("change-password");
    setMessage("");

    try {
      const payload = await accountRequest(
        "/auth/change-password",
        {
          method: "POST",
          body: JSON.stringify({
            current_password:
              securityForm.current_password,
            new_password:
              securityForm.new_password,
          }),
        },
      );

      setUser(payload.user || user);
      setSecurityForm((current) => ({
        ...current,
        current_password: "",
        new_password: "",
      }));
      setMessage(
        "Password changed. Other active sessions were signed out.",
      );
    } catch (error) {
      setMessage(error.message);
    } finally {
      setBusy("");
    }
  }


  async function logoutAllDevices() {
    const confirmed = window.confirm(
      "Log out this account from every device?",
    );

    if (!confirmed) {
      return;
    }

    setBusy("logout-all");
    setMessage("");

    try {
      await accountRequest(
        "/auth/logout-all",
        {
          method: "POST",
        },
      );

      setUser(null);
      setJourneys([]);
      setSessionState("guest");
      setSecurityForm({
        ...EMPTY_SECURITY_FORM,
      });
      setMessage(
        "You have been logged out from all devices.",
      );
    } catch (error) {
      setMessage(error.message);
    } finally {
      setBusy("");
    }
  }


  async function deleteAccount(event) {
    event.preventDefault();

    if (
      securityForm.delete_confirmation !==
      "DELETE MY ACCOUNT"
    ) {
      setMessage(
        'Type "DELETE MY ACCOUNT" exactly to continue.',
      );
      return;
    }

    const confirmed = window.confirm(
      "Permanently delete your RailYatra account and all cloud journeys? This cannot be undone.",
    );

    if (!confirmed) {
      return;
    }

    setBusy("delete-account");
    setMessage("");

    try {
      await accountRequest(
        "/auth/account",
        {
          method: "DELETE",
          body: JSON.stringify({
            password:
              securityForm.delete_password,
            confirmation:
              securityForm.delete_confirmation,
          }),
        },
      );

      setUser(null);
      setJourneys([]);
      setSessionState("guest");
      setSecurityForm({
        ...EMPTY_SECURITY_FORM,
      });
      setMessage(
        "Your RailYatra account was permanently deleted.",
      );
    } catch (error) {
      setMessage(error.message);
    } finally {
      setBusy("");
    }
  }


  async function saveCurrentJourney() {
    const source = normalizeCode(
      currentSource,
    );
    const destination = normalizeCode(
      currentDestination,
    );

    if (!source || !destination) {
      setMessage(
        "Enter both From and To stations before saving.",
      );
      return;
    }

    if (source === destination) {
      setMessage(
        "Source and destination must be different.",
      );
      return;
    }

    setBusy("save");
    setMessage("");

    try {
      await accountRequest(
        "/account/saved-journeys",
        {
          method: "POST",
          body: JSON.stringify({
            source,
            destination,
            journey_date:
              currentJourneyDate || "",
            class_code:
              currentClassCode || "SL",
            quota:
              currentQuota || "GN",
            label: `${source} to ${destination}`,
            note:
              "Saved from the RailYatra main search.",
          }),
        },
      );

      await refreshJourneys();

      setMessage(
        `${source} → ${destination} saved to your account.`,
      );
    } catch (error) {
      setMessage(error.message);
    } finally {
      setBusy("");
    }
  }

  async function importBrowserJourneys() {
    const browserJourneys =
      readBrowserSavedRoutes();

    if (!browserJourneys.length) {
      setMessage(
        "No browser-saved journeys were found.",
      );
      return;
    }

    setBusy("import");
    setMessage("");

    try {
      const payload = await accountRequest(
        "/account/saved-journeys/import",
        {
          method: "POST",
          body: JSON.stringify({
            journeys: browserJourneys,
          }),
        },
      );

      setJourneys(payload.journeys || []);

      setMessage(
        `${payload.processed_count} browser journey entries processed.`,
      );
    } catch (error) {
      setMessage(error.message);
    } finally {
      setBusy("");
    }
  }

  async function removeJourney(
    journeyId,
  ) {
    setBusy(`delete-${journeyId}`);
    setMessage("");

    try {
      await accountRequest(
        `/account/saved-journeys/${journeyId}`,
        {
          method: "DELETE",
        },
      );

      setJourneys((current) =>
        current.filter(
          (journey) =>
            journey.id !== journeyId,
        ),
      );

      setMessage(
        "Saved journey removed.",
      );
    } catch (error) {
      setMessage(error.message);
    } finally {
      setBusy("");
    }
  }

  function applyJourney(journey) {
    onApplyRoute?.(journey);

    setMessage(
      `Applied ${journey.source} → ${journey.destination}.`,
    );
  }

  return (
    <section
      className="user-account-panel"
      aria-label="RailYatra traveller account"
    >
      <div className="user-account-panel__heading">
        <div>
          <span>RailYatra account</span>
          <h2>
            Save journeys across devices
          </h2>
          <p>
            Search remains available without
            login. An account lets you keep
            journeys securely in the cloud.
          </p>
        </div>

        {sessionState ===
          "authenticated" && user && (
          <div className="user-account-panel__identity">
            <strong>
              {user.display_name}
            </strong>
            <span>{user.email}</span>
          </div>
        )}
      </div>

      {sessionState === "checking" && (
        <div
          className="user-account-panel__loading"
          role="status"
        >
          Checking account session…
        </div>
      )}

      {sessionState === "guest" && (
        <div className="user-account-panel__guest">
          <div className="user-account-panel__tabs">
            <button
              type="button"
              className={
                mode === "login"
                  ? "is-active"
                  : ""
              }
              onClick={() => {
                setMode("login");
                setMessage("");
              }}
            >
              Login
            </button>

            <button
              type="button"
              className={
                mode === "register"
                  ? "is-active"
                  : ""
              }
              onClick={() => {
                setMode("register");
                setMessage("");
              }}
            >
              Create account
            </button>
          </div>

          <form
            className="user-account-panel__form"
            onSubmit={
              submitAuthentication
            }
          >
            {mode === "register" && (
              <label>
                <span>Your name</span>
                <input
                  type="text"
                  value={form.display_name}
                  onChange={(event) =>
                    updateForm(
                      "display_name",
                      event.target.value,
                    )
                  }
                  autoComplete="name"
                  minLength={2}
                  maxLength={100}
                  required
                />
              </label>
            )}

            <label>
              <span>Email</span>
              <input
                type="email"
                value={form.email}
                onChange={(event) =>
                  updateForm(
                    "email",
                    event.target.value,
                  )
                }
                autoComplete="email"
                required
              />
            </label>

            <label>
              <span>Password</span>
              <input
                type="password"
                value={form.password}
                onChange={(event) =>
                  updateForm(
                    "password",
                    event.target.value,
                  )
                }
                autoComplete={
                  mode === "register"
                    ? "new-password"
                    : "current-password"
                }
                minLength={10}
                maxLength={128}
                required
              />
            </label>

            {mode === "register" && (
              <p className="user-account-panel__password-note">
                Use at least 10 characters,
                including a letter and a number.
              </p>
            )}

            <button
              type="submit"
              disabled={Boolean(busy)}
            >
              {busy === "authentication"
                ? "Please wait…"
                : mode === "register"
                  ? "Create account"
                  : "Login"}
            </button>
          </form>
        </div>
      )}

      {sessionState ===
        "authenticated" && user && (
        <div className="user-account-panel__account">
          <div className="user-account-panel__actions">
            <button
              type="button"
              onClick={saveCurrentJourney}
              disabled={Boolean(busy)}
            >
              {busy === "save"
                ? "Saving…"
                : "Save current journey"}
            </button>

            <button
              type="button"
              onClick={
                importBrowserJourneys
              }
              disabled={Boolean(busy)}
            >
              {busy === "import"
                ? "Importing…"
                : "Import browser journeys"}
            </button>

            <button
              type="button"
              className="user-account-panel__logout"
              onClick={logout}
              disabled={Boolean(busy)}
            >
              Logout
            </button>
          </div>

          <section
            className="user-account-panel__security"
            aria-label="Account security"
          >
            <div className="user-account-panel__security-heading">
              <div>
                <span>Account security</span>
                <strong>
                  Password and session controls
                </strong>
              </div>

              <p>
                Manage your password, active
                sessions and permanent account
                deletion.
              </p>
            </div>

            <div className="user-account-panel__security-grid">
              <form
                className="user-account-panel__security-card"
                onSubmit={changePassword}
              >
                <div>
                  <span>Password</span>
                  <strong>Change password</strong>
                  <p>
                    Changing your password signs
                    out every other active session.
                  </p>
                </div>

                <label>
                  <span>Current password</span>
                  <input
                    type="password"
                    value={
                      securityForm.current_password
                    }
                    onChange={(event) =>
                      updateSecurityForm(
                        "current_password",
                        event.target.value,
                      )
                    }
                    autoComplete="current-password"
                    minLength={1}
                    maxLength={128}
                    required
                  />
                </label>

                <label>
                  <span>New password</span>
                  <input
                    type="password"
                    value={
                      securityForm.new_password
                    }
                    onChange={(event) =>
                      updateSecurityForm(
                        "new_password",
                        event.target.value,
                      )
                    }
                    autoComplete="new-password"
                    minLength={10}
                    maxLength={128}
                    required
                  />
                </label>

                <p className="user-account-panel__security-note">
                  Use at least 10 characters,
                  including a letter and a number.
                </p>

                <button
                  type="submit"
                  disabled={Boolean(busy)}
                >
                  {busy === "change-password"
                    ? "Changing password…"
                    : "Change password"}
                </button>
              </form>

              <div className="user-account-panel__security-card">
                <div>
                  <span>Sessions</span>
                  <strong>
                    Log out all devices
                  </strong>
                  <p>
                    Revoke every active session,
                    including this browser.
                  </p>
                </div>

                <button
                  type="button"
                  className="is-warning"
                  onClick={logoutAllDevices}
                  disabled={Boolean(busy)}
                >
                  {busy === "logout-all"
                    ? "Logging out devices…"
                    : "Log out all devices"}
                </button>
              </div>

              <form
                className="user-account-panel__security-card user-account-panel__security-card--danger"
                onSubmit={deleteAccount}
              >
                <div>
                  <span>Danger zone</span>
                  <strong>
                    Delete account permanently
                  </strong>
                  <p>
                    Your account, sessions and
                    cloud journeys will be deleted.
                    This cannot be undone.
                  </p>
                </div>

                <label>
                  <span>Account password</span>
                  <input
                    type="password"
                    value={
                      securityForm.delete_password
                    }
                    onChange={(event) =>
                      updateSecurityForm(
                        "delete_password",
                        event.target.value,
                      )
                    }
                    autoComplete="current-password"
                    minLength={1}
                    maxLength={128}
                    required
                  />
                </label>

                <label>
                  <span>
                    Type DELETE MY ACCOUNT
                  </span>
                  <input
                    type="text"
                    value={
                      securityForm.delete_confirmation
                    }
                    onChange={(event) =>
                      updateSecurityForm(
                        "delete_confirmation",
                        event.target.value,
                      )
                    }
                    autoComplete="off"
                    required
                  />
                </label>

                <button
                  type="submit"
                  className="is-danger"
                  disabled={Boolean(busy)}
                >
                  {busy === "delete-account"
                    ? "Deleting account…"
                    : "Delete account permanently"}
                </button>
              </form>
            </div>
          </section>

          <div className="user-account-panel__saved-heading">
            <div>
              <span>Cloud journeys</span>
              <strong>
                {journeys.length} saved
              </strong>
            </div>

            <button
              type="button"
              onClick={async () => {
                setBusy("refresh");
                setMessage("");

                try {
                  await refreshJourneys();
                  setMessage(
                    "Saved journeys refreshed.",
                  );
                } catch (error) {
                  setMessage(error.message);
                } finally {
                  setBusy("");
                }
              }}
              disabled={Boolean(busy)}
            >
              Refresh
            </button>
          </div>

          {journeys.length === 0 ? (
            <div className="user-account-panel__empty">
              <strong>
                No cloud journeys saved yet
              </strong>
              <p>
                Enter a route in the main
                search and select Save current
                journey.
              </p>
            </div>
          ) : (
            <div className="user-account-panel__journeys">
              {journeys.map((journey) => (
                <article key={journey.id}>
                  <div>
                    <span>
                      {journey.label ||
                        "Saved journey"}
                    </span>
                    <strong>
                      {journey.source}
                      {" → "}
                      {journey.destination}
                    </strong>
                    <p>
                      {journey.journey_date ||
                        "Any date"}
                      {" · "}
                      {journey.class_code}
                      {" · "}
                      {journey.quota}
                    </p>
                  </div>

                  <div className="user-account-panel__journey-actions">
                    <button
                      type="button"
                      onClick={() =>
                        applyJourney(journey)
                      }
                    >
                      Use journey
                    </button>

                    <button
                      type="button"
                      className="is-danger"
                      onClick={() =>
                        removeJourney(
                          journey.id,
                        )
                      }
                      disabled={
                        busy ===
                        `delete-${journey.id}`
                      }
                    >
                      {busy ===
                      `delete-${journey.id}`
                        ? "Removing…"
                        : "Remove"}
                    </button>
                  </div>
                </article>
              ))}
            </div>
          )}
        </div>
      )}

      {message && (
        <p
          className="user-account-panel__message"
          role="status"
          aria-live="polite"
        >
          {message}
        </p>
      )}
    </section>
  );
}
