import AdminDashboardPreviewPanel from "./AdminDashboardPreviewPanel.jsx";

function adminPreviewEnabled() {
  if (typeof window === "undefined") return false;
  const params = new URLSearchParams(window.location.search);
  return params.get("admin") === "preview" || window.location.hash === "#admin";
}

export default function AdminDashboardGate() {
  if (!adminPreviewEnabled()) {
    return null;
  }
  return (
    <div className="admin-dashboard-gate">
      <AdminDashboardPreviewPanel />
    </div>
  );
}
