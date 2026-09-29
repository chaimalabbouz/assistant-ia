const API = import.meta.env.VITE_API_URL;

export async function apiLogin(email, password) {
  const res = await fetch(`${API}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ username: email, password }),
  });
  if (!res.ok) throw new Error("Email ou mot de passe incorrect");
  const data = await res.json();
  return data.access_token;
}

export async function apiChat(token, message, conversationId) {
  const res = await fetch(`${API}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ message, conversation_id: conversationId }),
  });
  if (res.status === 401) {
    const err = new Error("Session expirée, reconnecte-toi.");
    err.status = 401;
    throw err;
  }
  if (!res.ok) throw new Error("Erreur serveur, réessaie.");
  return res.json();
}