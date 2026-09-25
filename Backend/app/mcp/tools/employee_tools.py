"""
app/mcp/tools/employee_tools.py

Tools MCP pour les données employé.

Deux familles de fonctions :
- Self-scoped (my_*) : aucun employee_id en paramètre visible du LLM.
  L'identité est lue depuis le contexte de requête (résolu par le
  middleware à partir du JWT), jamais fournie par le modèle.
- department_info_tool : pas de donnée personnelle, reste ouvert.
"""

from app.mcp.context import get_context
from app.mcp.services.employee_service import (
    get_employee_profile as service_get_employee_profile,
    get_department_info as service_get_department_info,
    get_manager as service_get_manager,
    get_leave_balance as service_get_leave_balance,
)


def my_profile_tool() -> dict:
    """
    Retrieve the professional profile of the currently authenticated employee.
    """
    context = get_context()
    employee = service_get_employee_profile(context.employee_id)

    if employee is None:
        return {
            "success": False,
            "message": "Profile not found for the current employee.",
        }

    return {
        "success": True,
        "data": employee.model_dump(),
    }


def department_info_tool(department_id: str) -> dict:
    """
    Retrieve information about a company department.
    Not employee-sensitive data, no scoping needed.
    """
    department = service_get_department_info(department_id)

    if department is None:
        return {
            "success": False,
            "message": f"Department '{department_id}' not found.",
        }

    return {
        "success": True,
        "data": department.model_dump(),
    }


def my_manager_tool() -> dict:
    """
    Retrieve the manager of the currently authenticated employee.
    """
    context = get_context()
    manager = service_get_manager(context.employee_id)

    if manager is None:
        return {
            "success": False,
            "message": "No manager found for the current employee.",
        }

    return {
        "success": True,
        "data": manager.model_dump(),
    }


def my_leave_balance_tool() -> dict:
    """
    Retrieve the leave balances of the currently authenticated employee.
    """
    context = get_context()
    balances = service_get_leave_balance(context.employee_id)

    if not balances:
        return {
            "success": False,
            "message": "No leave balance found for the current employee.",
        }

    return {
        "success": True,
        "data": [balance.model_dump() for balance in balances],
    }