from app.mcp.services.employee_service import (
    get_employee_profile as service_get_employee_profile,
    get_department_info as service_get_department_info,
    get_manager as service_get_manager,
    get_leave_balance as service_get_leave_balance,
)


def employee_profile_tool(employee_id: str) -> dict:
    """
    Retrieve the professional profile of an employee.
    """

    employee = service_get_employee_profile(employee_id)

    if employee is None:
        return {
            "success": False,
            "message": f"Employee '{employee_id}' not found."
        }

    return {
        "success": True,
        "data": employee.model_dump()
    }


def department_info_tool(department_id: str) -> dict:
    """
    Retrieve information about a department.
    """

    department = service_get_department_info(department_id)

    if department is None:
        return {
            "success": False,
            "message": f"Department '{department_id}' not found."
        }

    return {
        "success": True,
        "data": department.model_dump()
    }


def manager_tool(employee_id: str) -> dict:
    """
    Retrieve the manager of an employee.
    """

    manager = service_get_manager(employee_id)

    if manager is None:
        return {
            "success": False,
            "message": (
                f"No manager found for employee '{employee_id}'."
            )
        }

    return {
        "success": True,
        "data": manager.model_dump()
    }


def leave_balance_tool(employee_id: str) -> dict:
    """
    Retrieve the leave balances of an employee.
    """

    balances = service_get_leave_balance(employee_id)

    if not balances:
        return {
            "success": False,
            "message": (
                f"No leave balance found for employee '{employee_id}'."
            )
        }

    return {
        "success": True,
        "data": [
            balance.model_dump()
            for balance in balances
        ]
    }