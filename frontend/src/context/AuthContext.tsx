import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { api } from "../api/client";
import { authToken } from "../api/auth";

type AuthUser = { id: string; email: string; is_admin: boolean };
type AuthContextValue = {
  user: AuthUser | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => void;
};
const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const onUnauthorized = () => setUser(null);
    window.addEventListener("sumi:unauthorized", onUnauthorized);
    if (!authToken.get()) { setLoading(false); return () => window.removeEventListener("sumi:unauthorized", onUnauthorized); }
    api.me().then(setUser).catch(() => { authToken.clear(); setUser(null); }).finally(() => setLoading(false));
    return () => window.removeEventListener("sumi:unauthorized", onUnauthorized);
  }, []);

  const value = useMemo<AuthContextValue>(() => ({
    user,
    loading,
    async signIn(email, password) {
      const token = await api.login(email, password);
      authToken.set(token.access_token);
      try { setUser(await api.me()); }
      catch (error) { authToken.clear(); throw error; }
    },
    signOut() { authToken.clear(); setUser(null); },
  }), [user, loading]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth debe utilizarse dentro de AuthProvider");
  return value;
}
