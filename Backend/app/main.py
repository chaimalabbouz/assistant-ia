"""
app/main.py

Point d'entrée de l'application FastAPI.
"""

from fastapi import FastAPI

from app.api.routes.auth import router as auth_router
from app.api.routes.users import router as users_router


app = FastAPI(title="HR Assistant API")

app.include_router(auth_router)
app.include_router(users_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}