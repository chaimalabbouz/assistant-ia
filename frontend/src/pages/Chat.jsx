import { useState, useRef, useEffect } from "react";
import Logo from "../components/Logo";
import ChatBubble from "../components/ChatBubble";
import { apiChat } from "../api";

const SUGGESTIONS = [
  "Quel est mon solde de congés ?",
  "Qui est mon manager ?",
  "Que dit la politique sur les congés maladie ?",
  "Comment poser un jour de congé ?",
];

function newConv() {
  return { id: crypto.randomUUID(), convId: null, title: "Nouvelle conversation", messages: [] };
}

function loadConvs() {
  try {
    const saved = JSON.parse(sessionStorage.getItem("convs"));
    if (saved?.length) return saved;
  } catch {
    // pas de conversations sauvegardées : on repart de zéro
  }
  return [newConv()];
}

export default function Chat({ token, onLogout }) {
  const [convs, setConvs] = useState(loadConvs);
  const [activeId, setActiveId] = useState(() => loadConvs()[0].id);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  const active = convs.find((c) => c.id === activeId) || convs[0];

  useEffect(() => {
    sessionStorage.setItem("convs", JSON.stringify(convs));
  }, [convs]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [active.messages, loading]);

  function update(id, fn) {
    setConvs((all) => all.map((c) => (c.id === id ? fn(c) : c)));
  }

  function startNew() {
    const c = newConv();
    setConvs((all) => [c, ...all]);
    setActiveId(c.id);
  }

  function remove(id) {
    const rest = convs.filter((c) => c.id !== id);
    if (rest.length === 0) {
      const c = newConv();
      setConvs([c]);
      setActiveId(c.id);
    } else {
      setConvs(rest);
      if (id === activeId) setActiveId(rest[0].id);
    }
  }

  async function send(raw) {
    const text = raw.trim();
    if (!text || loading) return;
    const id = active.id;
    const convId = active.convId;

    update(id, (c) => ({
      ...c,
      title: c.messages.length === 0 ? text.slice(0, 40) : c.title,
      messages: [...c.messages, { role: "user", text }],
    }));
    setInput("");
    setLoading(true);

    try {
      const data = await apiChat(token, text, convId);
      update(id, (c) => ({
        ...c,
        convId: data.conversation_id,
        messages: [...c.messages, { role: "bot", text: data.reply }],
      }));
    } catch (err) {
      if (err.status === 401) return onLogout();
      update(id, (c) => ({
        ...c,
        messages: [...c.messages, { role: "bot", text: err.message, error: true }],
      }));
    }
    setLoading(false);
  }

  return (
    <div className="chat-layout">
      <aside className="sidebar">
        <div className="brand"><Logo size={28} /> HR Nexus</div>
        <button className="btn" onClick={startNew}>+ Nouvelle conversation</button>
        <div className="conv-list">
          {convs.map((c) => (
            <div
              key={c.id}
              className={`conv ${c.id === active.id ? "on" : ""}`}
              onClick={() => setActiveId(c.id)}
            >
              <span>{c.title}</span>
              <button
                title="Supprimer"
                onClick={(e) => { e.stopPropagation(); remove(c.id); }}
              >✕</button>
            </div>
          ))}
        </div>
        <button className="btn ghost" onClick={onLogout}>Déconnexion</button>
      </aside>

      <main className="chat-main">
        <div className="messages">
          {active.messages.length === 0 && (
            <div className="empty">
              <Logo size={56} />
              <h2>Comment puis-je t'aider ?</h2>
              <p>Pose une question sur la politique RH ou sur tes données.</p>
              <div className="suggest">
                {SUGGESTIONS.map((s) => (
                  <button key={s} onClick={() => send(s)}>{s}</button>
                ))}
              </div>
            </div>
          )}

          {active.messages.map((m, i) => (
            <ChatBubble key={i} role={m.role} text={m.text} error={m.error} />
          ))}

          {loading && (
            <div className="bubble bot typing"><span /><span /><span /></div>
          )}
          <div ref={bottomRef} />
        </div>

        <form className="composer" onSubmit={(e) => { e.preventDefault(); send(input); }}>
          <input
            className="field"
            placeholder="Pose ta question RH..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
          />
          <button className="btn" disabled={loading}>Envoyer</button>
        </form>
      </main>
    </div>
  );
}