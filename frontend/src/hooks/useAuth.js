import { useState } from "react";
import { apiLogin } from "../api";

export function useAuth() {
  const [token, setToken] = useState(() => sessionStorage.getItem("token"));
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function login(email, password) {
    setError("");
    setLoading(true);
    try {
      const t = await apiLogin(email, password);
      sessionStorage.setItem("token", t);
      setToken(t);
    } catch (err) {
      setError(err.message);
    }
    setLoading(false);
  }

  function logout() {
    sessionStorage.removeItem("token");
    setToken(null);
  }

  return { token, error, setError, loading, login, logout };
}