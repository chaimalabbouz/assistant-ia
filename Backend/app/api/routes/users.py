"""
app/api/routes/users.py

Route de test pour valider le RequestContext (extraction de l'identité
depuis le JWT). Servira de base pour les futures routes self-scoped.
"""

from fastapi import APIRouter, Depends

from app.api.deps import get_current_context, RequestContext

router = APIRouter(tags=["users"])


@router.get("/me")
def read_current_user(context: RequestContext = Depends(get_current_context)) -> dict:
    """
    Retourne l'identité résolue depuis le token — permet de vérifier
    que le RequestContext fonctionne correctement de bout en bout.
    """
    return {
        "user_id": context.user_id,
        "employee_id": context.employee_id,
        "role": context.role,
        "is_hr_admin": context.is_hr_admin,
    }