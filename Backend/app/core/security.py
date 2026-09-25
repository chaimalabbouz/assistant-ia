"""
app/core/security.py

Utilitaires de sécurité :
- hashing et vérification des mots de passe (bcrypt)
- création et décodage des JWT

C'est ICI, et seulement ici, que le contenu du token (employee_id, role)
est décidé. Ces valeurs viennent de la base de données au moment du
login, jamais d'un input utilisateur ou LLM.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from passlib.context import CryptContext

from app.config import SECRET_KEY, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Hash un mot de passe en clair (utilisé au moment du seed des users de test)."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie un mot de passe en clair contre son hash stocké en base."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(*, user_id: str, employee_id: str, role: str) -> str:
    """
    Génère un JWT signé contenant l'identité résolue côté serveur.

    user_id, employee_id et role sont fournis par le backend APRÈS
    vérification du mot de passe — jamais par le client directement.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: dict[str, Any] = {
        "sub": user_id,
        "employee_id": employee_id,
        "role": role,
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Décode et valide un JWT.
    Lève jwt.ExpiredSignatureError si expiré, jwt.InvalidTokenError si invalide/falsifié.
    """
    return jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])