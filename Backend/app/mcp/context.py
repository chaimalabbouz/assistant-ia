"""
app/mcp/context.py

Contexte d'identité pour le serveur MCP, propagé via contextvars
(mécanisme standard de la bibliothèque Python, indépendant du
framework MCP lui-même).

Le middleware (voir middleware.py) peuple ce contexte une fois,
au début de chaque requête HTTP, à partir du JWT décodé. Les tools
self-scoped lisent ensuite ce contexte pour savoir "pour qui" agir,
sans jamais recevoir employee_id comme paramètre visible du LLM.
"""

from contextvars import ContextVar
from dataclasses import dataclass


@dataclass(frozen=True)
class MCPRequestContext:
    user_id: str
    employee_id: str
    role: str

    @property
    def is_hr_admin(self) -> bool:
        return self.role == "hr_admin"


_current_context: ContextVar[MCPRequestContext | None] = ContextVar(
    "_current_context", default=None
)


def set_context(context: MCPRequestContext) -> None:
    """Appelé par le middleware, une fois par requête."""
    _current_context.set(context)


def get_context() -> MCPRequestContext:
    """
    Appelé par les tools self-scoped pour connaître l'identité courante.

    Lève une erreur explicite si aucun contexte n'a été résolu —
    ça signifie que le middleware n'a pas fait son travail, ce qui
    ne doit jamais arriver en usage normal. Mieux vaut planter
    bruyamment ici que de silencieusement laisser passer une requête
    non authentifiée.
    """
    context = _current_context.get()
    if context is None:
        raise RuntimeError(
            "Aucun contexte d'identité résolu. "
            "Le middleware d'authentification MCP n'a pas été exécuté."
        )
    return context