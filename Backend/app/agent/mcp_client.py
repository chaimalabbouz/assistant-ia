"""
app/agent/mcp_client.py

Connexion cliente vers le serveur MCP (HR Employee MCP Server), avec
transmission du JWT de l'utilisateur courant à chaque requête.

IMPORTANT : contrairement au retriever RAG (singleton global, pas de
notion d'identité), ce client doit être créé PAR REQUÊTE, avec le
token de l'utilisateur courant — jamais partagé entre utilisateurs.
"""

from langchain_mcp_adapters.client import MultiServerMCPClient

MCP_SERVER_URL = "http://127.0.0.1:8001/mcp"


async def get_mcp_tools(access_token: str):
    """
    Se connecte au serveur MCP en transmettant le JWT dans le header
    Authorization, et retourne la liste des tools découverts (déjà
    convertis en objets LangChain Tool utilisables par l'agent).

    À appeler à chaque requête de chat, avec le token de l'utilisateur
    en cours — jamais mis en cache entre utilisateurs différents.
    """
    client = MultiServerMCPClient(
        {
            "hr_employee_server": {
                "url": MCP_SERVER_URL,
                "transport": "streamable_http",
                "headers": {
                    "Authorization": f"Bearer {access_token}",
                },
            }
        }
    )

    tools = await client.get_tools()
    return tools