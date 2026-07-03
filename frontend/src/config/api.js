const productionApiBase = "https://railyyatra-backend.onrender.com";
const developmentApiBase = import.meta.env.VITE_RAILYATRA_API_BASE || "http://127.0.0.1:8000";

export const API_BASE = (import.meta.env.PROD ? productionApiBase : developmentApiBase).replace(/\/$/, "");

export function apiUrl(path) {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE}${normalizedPath}`;
}
