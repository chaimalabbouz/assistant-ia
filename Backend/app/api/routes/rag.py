"""
app/api/routes/rag.py

Route de test pour valider que le retriever RAG est bien un service
partagé (singleton), et non réinstancié à chaque appel.
"""

from fastapi import APIRouter, Depends

from app.rag.hybrid_retriever import HybridRetriever
from app.rag.dependencies import get_retriever

router = APIRouter(prefix="/rag", tags=["rag"])


@router.get("/search")
def search(query: str, retriever: HybridRetriever = Depends(get_retriever)) -> dict:
    """
    Recherche hybride sur la policy RH.
    Base du futur tool RAG qui sera exposé à l'agent (Phase 3).
    """
    results = retriever.search(query, top_k=5)
    return {"query": query, "results": results}