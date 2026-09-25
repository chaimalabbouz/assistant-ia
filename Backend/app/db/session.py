"""
app/db/session.py

Point d'entrée unique pour la connexion à la base de données.
Toute l'application (routes, tools, futurs agents) doit passer par
ici pour obtenir une session DB, plutôt que de recréer un engine
à chaque fois (comme dans le script de validation initial).
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.config import DATABASE_URL

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """
    Dependency FastAPI : fournit une session DB par requête,
    et la ferme proprement à la fin, même en cas d'erreur.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()