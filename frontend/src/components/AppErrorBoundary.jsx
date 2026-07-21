import { Component } from "react";
import {
  recordFrontendError,
} from "../utils/frontendDiagnostics.js";
import "./AppErrorBoundary.css";

const SHOW_TECHNICAL_DETAILS =
  import.meta.env.DEV;

export default class AppErrorBoundary extends Component {
  constructor(props) {
    super(props);

    this.state = {
      hasError: false,
      message: "",
      referenceId: "",
    };
  }

  static getDerivedStateFromError(error) {
    return {
      hasError: true,
      message:
        error?.message ||
        "Unexpected frontend error",
    };
  }

  componentDidCatch(error, info) {
    const referenceId = recordFrontendError(
      error,
      {
        source: "react-error-boundary",
        componentStack: info?.componentStack,
      },
    );

    this.setState({ referenceId });
  }

  render() {
    if (!this.state.hasError) {
      return this.props.children;
    }

    return (
      <main className="app-error-boundary">
        <section
          className="app-error-boundary__card"
          role="alert"
          aria-live="assertive"
        >
          <p className="app-error-boundary__eyebrow">
            RailBay recovery
          </p>

          <h1>
            RailBay encountered a frontend error
          </h1>

          <p>
            Your browser did not remain on a blank
            page. Reload RailBay and try the action
            again.
          </p>

          {this.state.referenceId && (
            <p className="app-error-boundary__reference">
              Reference:{" "}
              <strong>
                {this.state.referenceId}
              </strong>
            </p>
          )}

          {SHOW_TECHNICAL_DETAILS && (
            <pre>
              {this.state.message}
            </pre>
          )}

          <div className="app-error-boundary__actions">
            <button
              type="button"
              onClick={() =>
                window.location.reload()
              }
            >
              Reload RailBay
            </button>

            <a href="/">
              Return home
            </a>
          </div>
        </section>
      </main>
    );
  }
}
