import Logo from "../components/Logo";

const features = [
  ["📘", "Politique RH", "Réponses sourcées à partir du manuel RH officiel de l'entreprise."],
  ["🏖️", "Solde de congés", "Consulte ton solde de congés en une phrase."],
  ["👤", "Profil et manager", "Retrouve tes informations et ton responsable."],
  ["🎫", "Tickets RH", "Une question sensible ? Elle est transmise à l'équipe RH."],
];

const steps = [
  ["Connecte-toi", "Avec ton compte professionnel."],
  ["Pose ta question", "En langage naturel, comme à un collègue."],
  ["Reçois une réponse", "Basée sur la politique RH et tes données."],
];

export default function Home({ onLogin }) {
  return (
    <div>
      <div className="nav">
        <div className="brand"><Logo /> HR Nexus</div>
        <button className="btn" onClick={onLogin}>Se connecter</button>
      </div>

      <section className="hero">
        <div>
          <h1>Ton assistant RH, <span className="grad-text">disponible 24h/24</span></h1>
          <p>
            HR Nexus répond à tes questions sur la politique de l'entreprise et
            accède à tes données personnelles : congés, profil, manager.
          </p>
          <div className="hero-actions">
            <button className="btn big" onClick={onLogin}>Commencer</button>
            <a href="#features"><button className="btn big ghost">En savoir plus</button></a>
          </div>
        </div>
        <div className="demo">
          <div className="b u">Combien de jours de congés me reste-t-il ?</div>
          <div className="b a">Il te reste 12 jours de congés annuels.</div>
          <div className="b u">Que dit la politique sur les congés maladie ?</div>
          <div className="b a">Selon la section 11.6, les congés maladie sont...</div>
        </div>
      </section>

      <section className="section" id="features">
        <h2>Ce que HR Nexus peut faire</h2>
        <div className="grid">
          {features.map(([ico, t, d]) => (
            <div className="card" key={t}>
              <div className="ico">{ico}</div>
              <h3>{t}</h3>
              <p>{d}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="section" style={{ paddingTop: 0 }}>
        <h2>Comment ça marche</h2>
        <div className="grid">
          {steps.map(([t, d], i) => (
            <div className="card" key={t}>
              <div className="step-num">{i + 1}</div>
              <h3>{t}</h3>
              <p>{d}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="privacy">
        <h2 style={{ margin: 0, fontSize: 30 }}>🔒 Tes données restent les tiennes</h2>
        <p>Chaque employé n'accède qu'à ses propres informations. HR Nexus n'a aucun moyen de lire les données d'un autre collègue.</p>
      </section>

      <div className="footer">© 2026 HR Nexus</div>
    </div>
  );
}