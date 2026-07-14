import {
  useEffect,
  useRef,
  useState,
} from "react";
import { apiUrl } from "../config/api.js";
import "./AccountRecoveryDialog.css";


const verificationRequestCache = new Map();


function readErrorMessage(payload, fallback) {
  return (
    payload?.error?.message ||
    payload?.detail ||
    payload?.message ||
    fallback
  );
}


async function recoveryRequest(
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
    throw new Error(
      readErrorMessage(
        payload,
        `Request failed with HTTP ${response.status}.`,
      ),
    );
  }

  return payload;
}


function clearRecoveryLocation() {
  if (typeof window === "undefined") {
    return;
  }

  const url = new URL(window.location.href);
  const cleanPath = url.pathname
    .replace(/\/+$/, "")
    .toLowerCase();

  if (
    cleanPath.endsWith("/verify-email") ||
    cleanPath.endsWith("/reset-password")
  ) {
    url.pathname = "/";
  }

  url.searchParams.delete("token");

  window.history.replaceState(
    {},
    "",
    `${url.pathname}${url.search}${url.hash}`,
  );
}


export default function AccountRecoveryDialog({
  dialog,
  initialEmail = "",
  onClose,
  onVerified,
  onPasswordReset,
}) {
  const mode = dialog?.mode || "";
  const token = dialog?.token || "";

  const [email, setEmail] =
    useState(initialEmail);
  const [newPassword, setNewPassword] =
    useState("");
  const [
    confirmPassword,
    setConfirmPassword,
  ] = useState("");
  const [status, setStatus] = useState({
    state: "idle",
    message: "",
  });

  const onVerifiedRef = useRef(onVerified);

  useEffect(() => {
    onVerifiedRef.current = onVerified;
  }, [onVerified]);

  useEffect(() => {
    if (!dialog) {
      return;
    }

    setEmail(initialEmail);
    setNewPassword("");
    setConfirmPassword("");
    setStatus({
      state: "idle",
      message: "",
    });
  }, [dialog, initialEmail]);

  useEffect(() => {
    if (mode !== "verify") {
      return;
    }

    if (!token) {
      setStatus({
        state: "error",
        message:
          "Verification link is missing its token.",
      });
      return;
    }

    let cancelled = false;

    setStatus({
      state: "loading",
      message: "Verifying your email address…",
    });

    const cacheKey = `verify:${token}`;
    let request =
      verificationRequestCache.get(cacheKey);

    if (!request) {
      request = recoveryRequest(
        "/auth/email-verification/confirm",
        {
          method: "POST",
          body: JSON.stringify({ token }),
        },
      );
      verificationRequestCache.set(
        cacheKey,
        request,
      );
    }

    request
      .then((payload) => {
        if (cancelled) {
          return;
        }

        setStatus({
          state: "success",
          message:
            payload?.message ||
            "Email address verified.",
        });

        onVerifiedRef.current?.(payload);
      })
      .catch((error) => {
        if (cancelled) {
          return;
        }

        setStatus({
          state: "error",
          message: error.message,
        });
      });

    return () => {
      cancelled = true;
    };
  }, [mode, token]);

  if (!dialog) {
    return null;
  }

  function closeDialog() {
    clearRecoveryLocation();
    onClose?.();
  }

  async function requestPasswordReset(event) {
    event.preventDefault();

    setStatus({
      state: "loading",
      message: "Requesting a reset link…",
    });

    try {
      const payload = await recoveryRequest(
        "/auth/forgot-password",
        {
          method: "POST",
          body: JSON.stringify({ email }),
        },
      );

      setStatus({
        state: "success",
        message:
          payload?.message ||
          "Check your email for a reset link.",
      });
    } catch (error) {
      setStatus({
        state: "error",
        message: error.message,
      });
    }
  }

  async function resetPassword(event) {
    event.preventDefault();

    if (newPassword !== confirmPassword) {
      setStatus({
        state: "error",
        message: "Passwords do not match.",
      });
      return;
    }

    if (!token) {
      setStatus({
        state: "error",
        message: "Reset link is missing its token.",
      });
      return;
    }

    setStatus({
      state: "loading",
      message: "Resetting your password…",
    });

    try {
      const payload = await recoveryRequest(
        "/auth/reset-password",
        {
          method: "POST",
          body: JSON.stringify({
            token,
            new_password: newPassword,
          }),
        },
      );

      clearRecoveryLocation();

      setStatus({
        state: "success",
        message:
          payload?.message ||
          "Password reset successfully.",
      });

      setNewPassword("");
      setConfirmPassword("");
      onPasswordReset?.(payload);
    } catch (error) {
      setStatus({
        state: "error",
        message: error.message,
      });
    }
  }

  const title =
    mode === "verify"
      ? "Verify your email"
      : mode === "reset"
        ? "Choose a new password"
        : "Reset your password";

  return (
    <div
      className="account-recovery-dialog"
      role="presentation"
    >
      <section
        className="account-recovery-dialog__card"
        role="dialog"
        aria-modal="true"
        aria-labelledby="account-recovery-title"
      >
        <div className="account-recovery-dialog__heading">
          <div>
            <span>RailYatra security</span>
            <h3 id="account-recovery-title">
              {title}
            </h3>
          </div>

          <button
            type="button"
            className="account-recovery-dialog__close"
            onClick={closeDialog}
            aria-label="Close account recovery"
          >
            ×
          </button>
        </div>

        {mode === "forgot" && (
          <form
            className="account-recovery-dialog__form"
            onSubmit={requestPasswordReset}
          >
            <p>
              Enter your account email. For
              security, RailYatra gives the same
              response whether or not an account
              exists.
            </p>

            <label>
              <span>Email</span>
              <input
                type="email"
                value={email}
                onChange={(event) =>
                  setEmail(event.target.value)
                }
                autoComplete="email"
                required
              />
            </label>

            <button
              type="submit"
              disabled={status.state === "loading"}
            >
              {status.state === "loading"
                ? "Requesting link…"
                : "Send reset link"}
            </button>
          </form>
        )}

        {mode === "reset" && (
          <form
            className="account-recovery-dialog__form"
            onSubmit={resetPassword}
          >
            <p>
              Use at least 10 characters with a
              letter and a number. Resetting your
              password signs out every active
              session.
            </p>

            <label>
              <span>New password</span>
              <input
                type="password"
                value={newPassword}
                onChange={(event) =>
                  setNewPassword(
                    event.target.value,
                  )
                }
                autoComplete="new-password"
                minLength={10}
                maxLength={128}
                required
              />
            </label>

            <label>
              <span>Confirm new password</span>
              <input
                type="password"
                value={confirmPassword}
                onChange={(event) =>
                  setConfirmPassword(
                    event.target.value,
                  )
                }
                autoComplete="new-password"
                minLength={10}
                maxLength={128}
                required
              />
            </label>

            <button
              type="submit"
              disabled={status.state === "loading"}
            >
              {status.state === "loading"
                ? "Resetting password…"
                : "Reset password"}
            </button>
          </form>
        )}

        {mode === "verify" && (
          <div className="account-recovery-dialog__verify">
            <p>
              RailYatra is checking this one-time
              verification link.
            </p>
          </div>
        )}

        {status.message && (
          <p
            className={[
              "account-recovery-dialog__status",
              `is-${status.state}`,
            ].join(" ")}
            role={
              status.state === "error"
                ? "alert"
                : "status"
            }
          >
            {status.message}
          </p>
        )}

        {status.state === "success" &&
          (mode === "verify" ||
            mode === "reset") && (
          <button
            type="button"
            className="account-recovery-dialog__continue"
            onClick={closeDialog}
          >
            Continue to RailYatra
          </button>
        )}
      </section>
    </div>
  );
}
