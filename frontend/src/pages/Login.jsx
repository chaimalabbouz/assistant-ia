import { useState } from "react";
import Logo from "../components/Logo";

export default function Login({ error, loading, onSubmit, onBack }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [show, setShow] = useState(false);

  function submit(e) {
    e.preventDefault();
    onSubmit(email, password);
  }

  return (
    <div className="login-page">
      <div className="login-side">
        <div className="brand" style={{ color: "#fff" }}><Logo /> HR Nexus</div>
        <h1>Ton assistant RH, toujours disponible</h1>
        <p>Politique de l'entreprise, congés, profil et manager : pose ta question en langage naturel.</p>
      </div>

      <div className="login-main">
        <button className="back-link" onClick={onBack}>← Retour</button>
        <form className="login-form" onSubmit={submit}>
          <h2>Connexion</h2>
          <p className="hint">Utilise ton compte professionnel.</p>
          <input className="field" placeholder="Email" value={email}
            onChange={(e) => setEmail(e.target.value)} autoFocus />
          <div className="pwd-wrap">
            <input className="field" type={show ? "text" : "password"} placeholder="Mot de passe"
              value={password} onChange={(e) => setPassword(e.target.value)} />
            <button type="button" onClick={() => setShow(!show)}>
              {show ? "Masquer" : "Afficher"}
            </button>
          </div>
          {error && <p style={{ color: "crimson", margin: 0, fontSize: 14 }}>{error}</p>}
          <button className="btn big" disabled={loading}>
            {loading ? "Connexion..." : "Se connecter"}
          </button>
          {loading && <p className="hint">Le serveur peut démarrer : compte jusqu'à 1 minute au premier appel.</p>}
        </form>
      </div>
    </div>
  );
}