import { Component } from "react";

export default class AppErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, message: "" };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, message: error?.message || "Unexpected frontend error" };
  }

  componentDidCatch(error) {
    console.error("RailBay UI error boundary:", error);
  }

  render() {
    if (this.state.hasError) {
      return (
        <main style={{ padding: "32px", fontFamily: "Inter, system-ui, sans-serif" }}>
          <section style={{ maxWidth: "760px", margin: "0 auto", padding: "24px", borderRadius: "20px", border: "1px solid #fecaca", background: "#fff1f2", color: "#7f1d1d" }}>
            <p style={{ margin: 0, fontSize: "12px", letterSpacing: "0.12em", textTransform: "uppercase", fontWeight: 800 }}>RailBay UI recovery</p>
            <h1 style={{ margin: "10px 0", fontSize: "28px" }}>Page recovered from a frontend error</h1>
            <p>The app did not go blank. Please hard refresh after the latest deploy.</p>
            <pre style={{ whiteSpace: "pre-wrap", background: "#ffffff", padding: "12px", borderRadius: "12px" }}>{this.state.message}</pre>
            <button onClick={() => window.location.reload()} style={{ padding: "10px 14px", border: 0, borderRadius: "999px", background: "#111827", color: "#ffffff", fontWeight: 800 }}>Reload RailBay</button>
          </section>
        </main>
      );
    }
    return this.props.children;
  }
}
