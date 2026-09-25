"""
app/main.py

Point d'entrée de l'application FastAPI.
Le HybridRetriever est initialisé une seule fois au démarrage (lifespan),
pas à chaque requête.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.auth import router as auth_router
from app.api.routes.users import router as users_router
from app.api.routes.rag import router as rag_router
from app.rag.hybrid_retriever import HybridRetriever


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup : ressources coûteuses initialisées une seule fois ---
    print("Initialisation du retriever RAG (BM25 + Cohere + Qdrant)...")
    app.state.retriever = HybridRetriever()
    print("Retriever RAG prêt.")

    yield

    # --- Shutdown ---
    print("Arrêt de l'application.")


app = FastAPI(title="HR Assistant API", lifespan=lifespan)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(rag_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}