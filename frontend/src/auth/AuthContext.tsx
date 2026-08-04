import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { api, getToken, setToken, type User } from "@/api/client";

type AuthState = {
  token: string | null;
  user: User | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  isAdmin: boolean;
};

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setTokenState] = useState<string | null>(() => getToken());
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function boot() {
      if (!token) {
        setUser(null);
        setLoading(false);
        return;
      }
      try {
        const me = await api.me();
        if (!cancelled) setUser(me);
      } catch {
        if (!cancelled) {
          setToken(null);
          setTokenState(null);
          setUser(null);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void boot();
    return () => {
      cancelled = true;
    };
  }, [token]);

  const login = useCallback(async (username: string, password: string) => {
    const { access_token } = await api.login(username, password);
    setToken(access_token);
    setTokenState(access_token);
    const me = await api.me();
    setUser(me);
  }, []);

  const logout = useCallback(() => {
    setToken(null);
    setTokenState(null);
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({
      token,
      user,
      loading,
      login,
      logout,
      isAdmin: user?.role === "admin",
    }),
    [token, user, loading, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth fora do AuthProvider");
  return ctx;
}
