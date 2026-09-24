"""
Test manuel de la recherche sémantique (embeddings seuls, baseline avant
d'ajouter BM25 + hybrid + reranking).

Prend une question, l'envoie à Cohere pour obtenir son embedding, puis
cherche les chunks les plus proches dans Qdrant.

Usage:
    python ingestion/test_search.py
"""

import os
import sys
from pathlib import Path

import cohere
from dotenv import load_dotenv
from qdrant_client import QdrantClient

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import QDRANT_HOST, QDRANT_PORT, QDRANT_COLLECTION_NAME

load_dotenv()

COHERE_MODEL = "embed-english-v3.0"

# Questions de test, volontairement choisies pour couvrir des cas simples
# et des cas ambigus (sujets proches sémantiquement)
TEST_QUESTIONS = [
    "How many sick days do employees get?",
    "What is the difference between vacation and PTO?",
    "What happens if an employee is harassed at work?",
    "Can I get leave for a family member's funeral?",
]


def search(co_client, qdrant_client, question: str, top_k: int = 3):
    embedding_response = co_client.embed(
        texts=[question],
        model=COHERE_MODEL,
        input_type="search_query",  # différent de "search_document" utilisé à l'ingestion
    )
    query_vector = embedding_response.embeddings[0]

    results = qdrant_client.search(
        collection_name=QDRANT_COLLECTION_NAME,
        query_vector=query_vector,
        limit=top_k,
    )
    return results


def main():
    cohere_api_key = os.getenv("COHERE_API_KEY")
    co = cohere.Client(cohere_api_key)
    qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    for question in TEST_QUESTIONS:
        print(f"\n{'=' * 70}")
        print(f"QUESTION: {question}")
        print("=" * 70)

        results = search(co, qdrant, question)

        for rank, r in enumerate(results, start=1):
            preview = r.payload["text"][:150].replace("\n", " ")
            print(
                f"\n  #{rank} | score={r.score:.4f} | "
                f"section={r.payload['section_id']} ({r.payload['title']})"
            )
            print(f"       {preview}...")


if __name__ == "__main__":
    main()