const fallbackApiBase = "http://127.0.0.1:8000";

export const API_BASE = (import.meta.env.VITE_RAILYATRA_API_BASE || fallbackApiBase).replace(/\/$/, "");

export function apiUrl(path) {
  const safePath = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE}${safePath}`;
}
