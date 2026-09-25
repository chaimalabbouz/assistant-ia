"""
app/mcp/server.py

Serveur MCP exposant les tools HR aux agents.

Transport : streamable-http, pour permettre au middleware d'authentification
(MCPAuthMiddleware) de lire le JWT depuis le header Authorization de chaque
requête HTTP entrante, et de résoudre l'identité avant l'exécution du tool.
"""

from mcp.server.fastmcp import FastMCP

from app.mcp.middleware import MCPAuthMiddleware
from app.mcp.tools.employee_tools import (
    my_profile_tool,
    department_info_tool,
    my_manager_tool,
    my_leave_balance_tool,
)


mcp = FastMCP("HR Employee MCP Server")


@mcp.tool()
def get_my_profile() -> dict:
    """
    Get the professional profile of the currently authenticated employee.

    Use this tool when you need information such as department,
    job title, employment type, manager, employment status or
    work location — always about the employee making the request.
    """
    return my_profile_tool()


@mcp.tool()
def get_department_info(department_id: str) -> dict:
    """
    Get information about a company department.
    """
    return department_info_tool(department_id)


@mcp.tool()
def get_my_manager() -> dict:
    """
    Get the current manager of the currently authenticated employee.
    """
    return my_manager_tool()


@mcp.tool()
def get_my_leave_balance() -> dict:
    """
    Get the leave balances of the currently authenticated employee.
    """
    return my_leave_balance_tool()


# Application ASGI exposée par FastMCP pour le transport HTTP,
# avec le middleware d'authentification monté dessus.
app = mcp.streamable_http_app()
app.add_middleware(MCPAuthMiddleware)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)