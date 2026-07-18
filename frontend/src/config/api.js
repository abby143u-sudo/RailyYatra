const fallbackApiBase = "http://127.0.0.1:8000";
const productionApiBase = "https://api.railbay.xyz";
const developmentApiBase = import.meta.env.VITE_RAILYATRA_API_BASE || fallbackApiBase;

export const API_BASE = (import.meta.env.PROD ? productionApiBase : developmentApiBase).replace(/\/$/, "");

export function apiUrl(path) {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE}${normalizedPath}`;
}
