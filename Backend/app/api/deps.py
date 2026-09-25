"""
app/api/deps.py

Dépendances FastAPI liées à l'authentification.

Le RequestContext est LA source de vérité pour l'identité de
l'utilisateur dans toute la suite de l'application. Toute route
ou tool qui a besoin de savoir "qui fait la requête" doit passer
par ici, jamais par un paramètre fourni ailleurs (body, LLM, etc.).
"""

from dataclasses import dataclass

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.security import decode_access_token

# tokenUrl pointe vers la future route de login (prochain fichier)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


@dataclass(frozen=True)
class RequestContext:
    """Identité résolue depuis le JWT, immuable pour la durée de la requête."""

    user_id: str
    employee_id: str
    role: str

    @property
    def is_hr_admin(self) -> bool:
        return self.role == "hr_admin"


def get_current_context(token: str = Depends(oauth2_scheme)) -> RequestContext:
    """
    Décode le JWT fourni dans le header Authorization et construit
    le RequestContext correspondant.

    Lève une 401 si le token est absent, invalide ou expiré.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Impossible de valider les identifiants.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expirée, veuillez vous reconnecter.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise credentials_exception

    user_id = payload.get("sub")
    employee_id = payload.get("employee_id")
    role = payload.get("role")

    if user_id is None or employee_id is None or role is None:
        raise credentials_exception

    return RequestContext(user_id=user_id, employee_id=employee_id, role=role)


def require_hr_admin(context: RequestContext = Depends(get_current_context)) -> RequestContext:
    """
    Dependency additionnelle pour protéger les routes réservées aux hr_admin.
    Utilisée plus tard pour le dashboard RH et les tools admin-scoped.
    """
    if not context.is_hr_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux administrateurs RH.",
        )
    return context