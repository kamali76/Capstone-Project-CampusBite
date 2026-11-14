import { useCallback, useEffect, useMemo, useState } from "react";
import { AuthContext } from "./AuthContext";
import { loginUser, registerUser } from "../api/auth";
import { TOKEN_KEY, USER_KEY } from "../utils/constants";

const readStoredUser = () => {
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
};

export default function AuthProvider({ children }) {
  // Lazy initial state: restores the session from localStorage on page load
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY));
  const [user, setUser] = useState(readStoredUser);

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    setToken(null);
    setUser(null);
  }, []);

  const login = useCallback(async (email, password) => {
    const { data } = await loginUser(email, password);
    localStorage.setItem(TOKEN_KEY, data.access_token);
    localStorage.setItem(USER_KEY, JSON.stringify(data.user));
    setToken(data.access_token);
    setUser(data.user);
    return data.user;
  }, []);

  const register = useCallback(async (payload) => {
    const { data } = await registerUser(payload);
    return data;
  }, []);

  // Listen for the 401 event fired by the axios interceptor (expired/invalid token)
  useEffect(() => {
    window.addEventListener("auth:logout", logout);
    return () => window.removeEventListener("auth:logout", logout);
  }, [logout]);

  // useMemo avoids re-rendering every consumer when nothing changed
  const value = useMemo(
    () => ({ user, token, isAuthenticated: Boolean(token && user), login, register, logout }),
    [user, token, login, register, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
