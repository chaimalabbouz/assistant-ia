import { useState, useRef, useEffect } from "react";
import Logo from "../components/Logo";
import { apiChat } from "../api";

export default function Chat({ token, onLogout }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [convId, setConvId] = useState(null);
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function send(e) {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading) return;
    setMessages((m) => [...m, { role: "user", text }]);
    setInput("");
    setLoading(true);
    try {
      const data = await apiChat(token, text, convId);
      setConvId(data.conversation_id);
      setMessages((m) => [...m, { role: "bot", text: data.reply }]);
    } catch (err) {
      if (err.status === 401) return onLogout();
      setMessages((m) => [...m, { role: "bot", text: err.message }]);
    }
    setLoading(false);
  }

  return (
    <div style={styles.chat}>
      <div style={styles.header}>
        <div className="brand"><Logo size={28} /> HR Nexus</div>
        <button className="btn ghost" onClick={onLogout}>Déconnexion</button>
      </div>
      <div style={styles.messages}>
        {messages.map((m, i) => (
          <div key={i} style={{
            ...styles.bubble,
            alignSelf: m.role === "user" ? "flex-end" : "flex-start",
            background: m.role === "user" ? "#2563eb" : "#e5e7eb",
            color: m.role === "user" ? "#fff" : "#111",
          }}>
            {m.text}
          </div>
        ))}
        {loading && <div style={{ color: "#666" }}>L'assistant réfléchit...</div>}
        <div ref={bottomRef} />
      </div>
      <form onSubmit={send} style={styles.form}>
        <input className="field" style={{ flex: 1 }} placeholder="Pose ta question RH..."
          value={input} onChange={(e) => setInput(e.target.value)} />
        <button className="btn" disabled={loading}>Envoyer</button>
      </form>
    </div>
  );
}

const styles = {
  chat: { display: "flex", flexDirection: "column", height: "100vh", maxWidth: 800, margin: "0 auto" },
  header: { display: "flex", justifyContent: "space-between", alignItems: "center", padding: 12, borderBottom: "1px solid #e2e8f0" },
  messages: { flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: 8, padding: 16 },
  bubble: { maxWidth: "75%", padding: "10px 14px", borderRadius: 14, whiteSpace: "pre-wrap" },
  form: { display: "flex", gap: 8, padding: 12, borderTop: "1px solid #e2e8f0" },
};