"""
app/ingestion/embed_and_store.py

Génère les embeddings Cohere pour tous les chunks et les insère dans Qdrant.
"""

import json
import os
from pathlib import Path

import cohere
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.config import (
    CHUNKS_PATH,
    QDRANT_HOST,
    QDRANT_PORT,
    QDRANT_URL,
    QDRANT_API_KEY,
    QDRANT_COLLECTION_NAME,
)

COHERE_MODEL = "embed-english-v3.0"
EMBEDDING_DIM = 1024


def load_chunks(path: Path) -> list[dict]:
    chunks = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            chunks.append(json.loads(line))
    return chunks


def get_embeddings(co_client: cohere.Client, texts: list[str]) -> list[list[float]]:
    response = co_client.embed(
        texts=texts,
        model=COHERE_MODEL,
        input_type="search_document",
    )
    return response.embeddings


def make_qdrant_client() -> QdrantClient:
    if QDRANT_URL:
        print(f"Connexion à Qdrant Cloud : {QDRANT_URL}")
        return QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=120)
    print(f"Connexion à Qdrant local : {QDRANT_HOST}:{QDRANT_PORT}")
    return QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)


def recreate_collection(qdrant: QdrantClient):
    existing = [c.name for c in qdrant.get_collections().collections]
    if QDRANT_COLLECTION_NAME in existing:
        print(f"Collection '{QDRANT_COLLECTION_NAME}' existe déjà, suppression et recréation.")
        qdrant.delete_collection(QDRANT_COLLECTION_NAME)

    qdrant.create_collection(
        collection_name=QDRANT_COLLECTION_NAME,
        vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
    )
    print(f"Collection '{QDRANT_COLLECTION_NAME}' créée.")


def main():
    cohere_api_key = os.getenv("COHERE_API_KEY")
    if not cohere_api_key:
        raise ValueError("COHERE_API_KEY introuvable. Vérifie ton fichier .env.")

    if not CHUNKS_PATH.exists():
        raise FileNotFoundError(f"{CHUNKS_PATH} introuvable. Lance d'abord ingestion/chunker.py.")

    chunks = load_chunks(CHUNKS_PATH)
    print(f"{len(chunks)} chunks chargés depuis {CHUNKS_PATH}")

    co = cohere.Client(cohere_api_key)
    qdrant = make_qdrant_client()

    recreate_collection(qdrant)

    BATCH_SIZE = 96
    point_id = 0
    total = 0

    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        texts = [c["text"] for c in batch]

        print(f"Embeddings des chunks {i} à {i + len(batch)}...")
        embeddings = get_embeddings(co, texts)

        points = []
        for chunk, vector in zip(batch, embeddings):
            points.append(
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "chunk_id": chunk["chunk_id"],
                        "section_id": chunk["section_id"],
                        "title": chunk["title"],
                        "text": chunk["text"],
                    },
                )
            )
            point_id += 1

        # On envoie à Qdrant batch par batch (et non tout à la fin)
        qdrant.upsert(collection_name=QDRANT_COLLECTION_NAME, points=points)
        total += len(points)
        print(f"  -> {total} points insérés")

    count = qdrant.count(collection_name=QDRANT_COLLECTION_NAME).count
    print(f"Vérification : {count} points présents dans la collection.")


if __name__ == "__main__":
    main()