import { useState, useRef, useEffect } from "react";

const API = import.meta.env.VITE_API_URL;

export default function App() {
  const [token, setToken] = useState(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [convId, setConvId] = useState(null);
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function login(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await fetch(`${API}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({ username: email, password }),
      });
      if (!res.ok) throw new Error("Email ou mot de passe incorrect");
      const data = await res.json();
      setToken(data.access_token);
    } catch (err) {
      setError(err.message);
    }
    setLoading(false);
  }

  async function send(e) {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading) return;
    setMessages((m) => [...m, { role: "user", text }]);
    setInput("");
    setLoading(true);
    try {
      const res = await fetch(`${API}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ message: text, conversation_id: convId }),
      });
      if (res.status === 401) {
        setToken(null);
        throw new Error("Session expirée, reconnecte-toi.");
      }
      if (!res.ok) throw new Error("Erreur serveur, réessaie.");
      const data = await res.json();
      setConvId(data.conversation_id);
      setMessages((m) => [...m, { role: "bot", text: data.reply }]);
    } catch (err) {
      setMessages((m) => [...m, { role: "bot", text: err.message }]);
    }
    setLoading(false);
  }

  function logout() {
    setToken(null);
    setMessages([]);
    setConvId(null);
    setPassword("");
  }

  if (!token) {
    return (
      <div style={styles.center}>
        <form onSubmit={login} style={styles.card}>
          <h2>Assistant RH</h2>
          <input
            style={styles.input}
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <input
            style={styles.input}
            type="password"
            placeholder="Mot de passe"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          {error && <p style={{ color: "crimson" }}>{error}</p>}
          <button style={styles.button} disabled={loading}>
            {loading ? "Connexion... (peut prendre 1 min)" : "Se connecter"}
          </button>
        </form>
      </div>
    );
  }

  return (
    <div style={styles.chat}>
      <div style={styles.header}>
        <b>Assistant RH</b>
        <button onClick={logout}>Déconnexion</button>
      </div>
      <div style={styles.messages}>
        {messages.map((m, i) => (
          <div
            key={i}
            style={{
              ...styles.bubble,
              alignSelf: m.role === "user" ? "flex-end" : "flex-start",
              background: m.role === "user" ? "#2563eb" : "#e5e7eb",
              color: m.role === "user" ? "#fff" : "#111",
            }}
          >
            {m.text}
          </div>
        ))}
        {loading && <div style={{ color: "#666" }}>L'assistant réfléchit...</div>}
        <div ref={bottomRef} />
      </div>
      <form onSubmit={send} style={styles.form}>
        <input
          style={{ ...styles.input, flex: 1 }}
          placeholder="Pose ta question RH..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        <button style={styles.button} disabled={loading}>
          Envoyer
        </button>
      </form>
    </div>
  );
}

const styles = {
  center: { display: "flex", justifyContent: "center", alignItems: "center", height: "100vh" },
  card: { display: "flex", flexDirection: "column", gap: 12, width: 320, padding: 24, border: "1px solid #ddd", borderRadius: 12 },
  input: { padding: 10, borderRadius: 8, border: "1px solid #ccc", fontSize: 15 },
  button: { padding: "10px 16px", borderRadius: 8, border: "none", background: "#2563eb", color: "#fff", cursor: "pointer" },
  chat: { display: "flex", flexDirection: "column", height: "100vh", maxWidth: 800, margin: "0 auto" },
  header: { display: "flex", justifyContent: "space-between", alignItems: "center", padding: 12, borderBottom: "1px solid #ddd" },
  messages: { flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: 8, padding: 16 },
  bubble: { maxWidth: "75%", padding: "10px 14px", borderRadius: 14, whiteSpace: "pre-wrap" },
  form: { display: "flex", gap: 8, padding: 12, borderTop: "1px solid #ddd" },
};