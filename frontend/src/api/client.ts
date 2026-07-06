// Client HTTP central : jeton JWT automatique + refresh transparent sur 401.
import axios from "axios";

const api = axios.create({ baseURL: "/api" });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

let refreshing: Promise<{ data: { access_token: string; refresh_token: string } }> | null = null;

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    const refreshToken = localStorage.getItem("refresh_token");
    if (error.response?.status === 401 && refreshToken && !original._retried) {
      original._retried = true;
      try {
        refreshing = refreshing ?? axios.post("/api/auth/refresh", { refresh_token: refreshToken });
        const { data } = await refreshing;
        refreshing = null;
        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("refresh_token", data.refresh_token);
        original.headers.Authorization = `Bearer ${data.access_token}`;
        return api(original);
      } catch {
        refreshing = null;
        localStorage.clear();
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

/** Extrait un message d'erreur lisible d'une réponse FastAPI. */
export function apiError(err: unknown, fallback = "Une erreur est survenue"): string {
  if (axios.isAxiosError(err)) {
    const detail = err.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) return "Formulaire invalide — vérifiez les champs.";
  }
  return fallback;
}

export default api;
