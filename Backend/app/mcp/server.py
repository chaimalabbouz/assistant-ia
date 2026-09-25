from mcp.server.fastmcp import FastMCP

from app.mcp.tools.employee_tools import (
    employee_profile_tool,
    department_info_tool,
    manager_tool,
    leave_balance_tool,
)


mcp = FastMCP("HR Employee MCP Server")


@mcp.tool()
def get_employee_profile(employee_id: str) -> dict:
    """
    Get the professional profile of an employee.

    Use this tool when you need information such as
    department, job title, employment type, manager,
    employment status or work location.
    """

    return employee_profile_tool(employee_id)


@mcp.tool()
def get_department_info(department_id: str) -> dict:
    """
    Get information about a company department.
    """

    return department_info_tool(department_id)


@mcp.tool()
def get_manager(employee_id: str) -> dict:
    """
    Get the current manager of an employee.
    """

    return manager_tool(employee_id)


@mcp.tool()
def get_leave_balance(employee_id: str) -> dict:
    """
    Get the leave balances of an employee.
    """

    return leave_balance_tool(employee_id)


if __name__ == "__main__":
    mcp.run()