"""
app/mcp/middleware.py

Middleware HTTP pour le serveur MCP : intercepte chaque requête,
décode le JWT présent dans le header Authorization, et peuple le
contexte d'identité (app/mcp/context.py) avant que le tool ne s'exécute.

Réutilise exactement la même logique de décodage que l'API principale
(app/core/security.py) — pas de nouvelle logique d'auth inventée ici.
"""

import jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.security import decode_access_token
from app.mcp.context import set_context, MCPRequestContext


class MCPAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        auth_header = request.headers.get("Authorization")

        if auth_header is None or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"error": "Authorization header manquant ou mal formé."},
            )

        token = auth_header.removeprefix("Bearer ").strip()

        try:
            payload = decode_access_token(token)
        except jwt.ExpiredSignatureError:
            return JSONResponse(
                status_code=401,
                content={"error": "Token expiré."},
            )
        except jwt.InvalidTokenError:
            return JSONResponse(
                status_code=401,
                content={"error": "Token invalide."},
            )

        user_id = payload.get("sub")
        employee_id = payload.get("employee_id")
        role = payload.get("role")

        if user_id is None or employee_id is None or role is None:
            return JSONResponse(
                status_code=401,
                content={"error": "Token incomplet."},
            )

        set_context(
            MCPRequestContext(user_id=user_id, employee_id=employee_id, role=role)
        )

        response = await call_next(request)
        return response