// Authentification : profil courant, login/logout, page d'accueil par rôle.
import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import api from "@/api/client";
import type { Role, User } from "@/api/types";

export const ROLE_HOME: Record<Role, string> = {
  advisor: "/clients",
  director: "/dashboard",
  admin: "/users",
};
export const ROLE_LABEL: Record<Role, string> = {
  advisor: "Conseiller",
  director: "Directeur d'agence",
  admin: "Administrateur",
};

interface AuthValue {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<User>;
  logout: () => void;
}

const AuthContext = createContext<AuthValue>(null as unknown as AuthValue);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!localStorage.getItem("access_token")) {
      setLoading(false);
      return;
    }
    api
      .get<User>("/auth/me")
      .then(({ data }) => setUser(data))
      .catch(() => localStorage.clear())
      .finally(() => setLoading(false));
  }, []);

  async function login(email: string, password: string) {
    const form = new URLSearchParams({ username: email, password });
    const { data } = await api.post("/auth/login", form);
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
    const me = await api.get<User>("/auth/me");
    setUser(me.data);
    return me.data;
  }

  function logout() {
    localStorage.clear();
    setUser(null);
    window.location.href = "/login";
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>{children}</AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
