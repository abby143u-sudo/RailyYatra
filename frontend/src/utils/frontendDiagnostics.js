const STORAGE_KEY = "railbay_frontend_diagnostics";
const MAX_REPORTS = 12;

function safeText(value, maximumLength = 300) {
  return String(value || "")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, maximumLength);
}

function createReferenceId() {
  const randomPart =
    typeof crypto !== "undefined" &&
    typeof crypto.randomUUID === "function"
      ? crypto.randomUUID().slice(0, 8)
      : Math.random().toString(36).slice(2, 10);

  return `RB-${Date.now().toString(36)}-${randomPart}`.toUpperCase();
}

function normalizeError(error) {
  if (error instanceof Error) {
    return {
      name: safeText(error.name, 80) || "Error",
      message:
        safeText(error.message, 300) ||
        "Unexpected frontend error",
    };
  }

  return {
    name: "Error",
    message:
      safeText(error, 300) ||
      "Unexpected frontend error",
  };
}

function saveReport(report) {
  if (
    typeof window === "undefined" ||
    !window.sessionStorage
  ) {
    return;
  }

  try {
    const existing = JSON.parse(
      window.sessionStorage.getItem(STORAGE_KEY) ||
        "[]",
    );

    const reports = Array.isArray(existing)
      ? existing
      : [];

    reports.unshift(report);

    window.sessionStorage.setItem(
      STORAGE_KEY,
      JSON.stringify(reports.slice(0, MAX_REPORTS)),
    );
  } catch {
    return;
  }
}

export function recordFrontendError(
  error,
  context = {},
) {
  const normalized = normalizeError(error);
  const referenceId = createReferenceId();

  const report = {
    reference_id: referenceId,
    occurred_at: new Date().toISOString(),
    name: normalized.name,
    message: normalized.message,
    source:
      safeText(context.source, 80) ||
      "frontend",
    path:
      typeof window !== "undefined"
        ? window.location.pathname
        : "",
  };

  if (
    import.meta.env.DEV &&
    context.componentStack
  ) {
    report.component_stack = safeText(
      context.componentStack,
      800,
    );
  }

  saveReport(report);

  console.error(
    `RailBay frontend error ${referenceId}:`,
    error,
  );

  return referenceId;
}

export function installGlobalFrontendDiagnostics() {
  if (
    typeof window === "undefined" ||
    window.__railbayDiagnosticsInstalled
  ) {
    return;
  }

  window.__railbayDiagnosticsInstalled = true;

  window.addEventListener("error", (event) => {
    recordFrontendError(
      event.error || event.message,
      {
        source: "window.error",
      },
    );
  });

  window.addEventListener(
    "unhandledrejection",
    (event) => {
      recordFrontendError(event.reason, {
        source: "unhandledrejection",
      });
    },
  );
}
