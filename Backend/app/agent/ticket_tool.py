"""
app/agent/ticket_tool.py

Tool LangChain pour la création de tickets RH, utilisé par l'agent
quand une question sort de son scope (litige, harcèlement, négociation
salariale, question sans réponse fiable dans la policy, etc.).

Comme pour les tools MCP self-scoped, employee_id vient du contexte
authentifié (JWT déjà décodé), jamais du LLM — seuls question et
category sont fournis par le modèle.
"""

from langchain_core.tools import tool

from app.mcp.services.ticket_service import create_ticket

HR_CONTACT_EMAIL = "hr@company.com"


def make_create_hr_ticket_tool(employee_id: str):
    """
    Factory : crée le tool en fermeture sur l'employee_id de l'utilisateur
    courant, résolu depuis le RequestContext au moment de la construction
    de l'agent (voir graph.py) — jamais fourni par le LLM.
    """

    @tool
    def create_hr_ticket(question: str, category: str) -> str:
        """
        Escalate a question to the HR team by creating a ticket, instead
        of attempting to answer it yourself. Use this tool when a question
        is outside your scope: legal disputes, harassment or discrimination
        concerns, salary negotiation, personal data changes, or any topic
        you cannot answer reliably from the HR policy or the employee's
        own data.

        Args:
            question: the employee's original question, as asked.
            category: one of "legal", "harassment", "salary",
                "personal_data", or "other".
        """
        ticket = create_ticket(
            employee_id=employee_id,
            question=question,
            category=category,
        )

        return (
            f"A ticket has been created (ID: {ticket.ticket_id}) and forwarded "
            f"to the HR team at {HR_CONTACT_EMAIL}. They will follow up with you "
            f"directly regarding this request."
        )

    return create_hr_ticket