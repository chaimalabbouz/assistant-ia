"""
app/api/routes/tickets.py

Route de consultation des tickets RH. Un employé ne voit que ses
propres tickets ; un hr_admin voit tous les tickets.
"""

from fastapi import APIRouter, Depends

from app.api.deps import get_current_context, RequestContext
from app.mcp.services.ticket_service import get_tickets_for_employee, get_all_tickets

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.get("")
def list_tickets(context: RequestContext = Depends(get_current_context)) -> list[dict]:
    """
    Retourne les tickets visibles par l'utilisateur courant :
    - hr_admin : tous les tickets de l'entreprise
    - employee : uniquement ses propres tickets
    """
    if context.is_hr_admin:
        tickets = get_all_tickets()
    else:
        tickets = get_tickets_for_employee(context.employee_id)

    return [t.model_dump() for t in tickets]