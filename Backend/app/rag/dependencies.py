"""
app/rag/dependencies.py

Fournit un accès à l'instance UNIQUE de HybridRetriever, initialisée
une seule fois au démarrage de l'application (voir app/main.py).
"""

from fastapi import Request

from app.rag.hybrid_retriever import HybridRetriever


def get_retriever(request: Request) -> HybridRetriever:
    """
    Dependency FastAPI : retourne l'instance de HybridRetriever déjà
    créée au démarrage du serveur, stockée dans app.state.

    Ne JAMAIS faire HybridRetriever() ici directement — ça rechargerait
    tout l'index BM25 et reconnecterait Cohere/Qdrant à chaque requête.
    """
    return request.app.state.retriever