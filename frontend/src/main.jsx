import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App.jsx";
import AppErrorBoundary from "./components/AppErrorBoundary.jsx";
import { installRailYatraRouteCompatibility } from "./utils/routeCompatibilityRuntime.js";
import "./index.css";
import BetaFeedbackWidget from "./components/BetaFeedbackWidget.jsx";
import AdminBetaFeedbackPanel from "./components/AdminBetaFeedbackPanel.jsx";

installRailYatraRouteCompatibility();

const showInternalTools =
  import.meta.env.DEV ||
  new URLSearchParams(window.location.search).get("internal") ===
    "1";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <AppErrorBoundary>
      <>
        <App />
        <BetaFeedbackWidget />
        {showInternalTools && <AdminBetaFeedbackPanel />}
      </>
    </AppErrorBoundary>
  </StrictMode>,
);
