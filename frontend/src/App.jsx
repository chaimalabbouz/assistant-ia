import { useState } from "react";
import { useAuth } from "./hooks/useAuth";
import Home from "./pages/Home";
import Login from "./pages/Login";
import Chat from "./pages/Chat";

export default function App() {
  const { token, error, setError, loading, login, logout } = useAuth();
  const [page, setPage] = useState("home");

  if (token) return <Chat token={token} onLogout={() => { logout(); setPage("home"); }} />;

  if (page === "login") {
    return (
      <Login
        error={error}
        loading={loading}
        onSubmit={login}
        onBack={() => { setPage("home"); setError(""); }}
      />
    );
  }

  return <Home onLogin={() => setPage("login")} />;
}