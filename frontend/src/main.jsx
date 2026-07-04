import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App.jsx";
import AppErrorBoundary from "./components/AppErrorBoundary.jsx";
import { installRailYatraRouteCompatibility } from "./utils/routeCompatibilityRuntime.js";
import "./index.css";
import BetaFeedbackWidget from "./components/BetaFeedbackWidget.jsx";

installRailYatraRouteCompatibility();

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <AppErrorBoundary>
      <>
      <App />
      <BetaFeedbackWidget />
    </>
    </AppErrorBoundary>
  </StrictMode>
);
