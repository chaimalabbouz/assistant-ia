"""
app/main.py
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.auth import router as auth_router
from app.api.routes.users import router as users_router
from app.api.routes.rag import router as rag_router
from app.rag.hybrid_retriever import HybridRetriever
from app.agent.checkpointer import init_checkpointer, close_checkpointer
from app.api.routes.chat import router as chat_router
from app.api.routes.tickets import router as tickets_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Initialisation du retriever RAG (BM25 + Cohere + Qdrant)...")
    app.state.retriever = HybridRetriever()
    print("Retriever RAG prêt.")

    print("Initialisation du checkpointer (mémoire conversationnelle)...")
    app.state.checkpointer = await init_checkpointer()
    print("Checkpointer prêt.")

    yield
    await close_checkpointer()
    print("Arrêt de l'application.")


app = FastAPI(title="HR Assistant API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(rag_router)
app.include_router(chat_router)
app.include_router(tickets_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}