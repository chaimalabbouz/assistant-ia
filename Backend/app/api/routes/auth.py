"""
app/api/routes/auth.py

Endpoint de connexion : vérifie les identifiants contre la table `users`
et retourne un JWT signé contenant l'identité résolue côté serveur.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import User
from app.core.security import verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> dict:
    """
    OAuth2PasswordRequestForm attend des champs `username` et `password`
    (standard FastAPI). On utilise `username` comme étant l'email de connexion.
    """
    user = db.query(User).filter(User.email == form_data.username).first()

    generic_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Email ou mot de passe incorrect.",
    )

    if user is None:
        raise generic_error

    if not verify_password(form_data.password, user.password_hash):
        raise generic_error

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ce compte est désactivé.",
        )

    token = create_access_token(
        user_id=user.user_id,
        employee_id=user.employee_id,
        role=user.role,
    )

    user.last_login = datetime.now(timezone.utc)
    db.commit()

    return {
        "access_token": token,
        "token_type": "bearer",
    }