
import json
import sys
from pathlib import Path
 
import cohere
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
 
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import CHUNKS_PATH, QDRANT_HOST, QDRANT_PORT, QDRANT_COLLECTION_NAME
 
import os
 
# Charge les variables du fichier .env (dont COHERE_API_KEY)
load_dotenv()
 
COHERE_MODEL = "embed-english-v3.0"  # le manuel est en anglais
EMBEDDING_DIM = 1024  # dimension du vecteur produit par ce modèle Cohere
 
 
def load_chunks(path: Path) -> list[dict]:
    chunks = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            chunks.append(json.loads(line))
    return chunks
 
 
def get_embeddings(co_client: cohere.Client, texts: list[str]) -> list[list[float]]:
    """
    Appelle l'API Cohere pour obtenir les embeddings d'une liste de textes.
    input_type="search_document" car ce sont des documents à indexer
    (différent de "search_query" utilisé plus tard pour les questions).
    """
    response = co_client.embed(
        texts=texts,
        model=COHERE_MODEL,
        input_type="search_document",
    )
    return response.embeddings
 
 
def create_collection_if_not_exists(qdrant: QdrantClient):
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
        raise ValueError(
            "COHERE_API_KEY introuvable. Vérifie ton fichier .env à la racine du projet."
        )
 
    if not CHUNKS_PATH.exists():
        raise FileNotFoundError(
            f"{CHUNKS_PATH} introuvable. Lance d'abord ingestion/chunker.py."
        )
 
    chunks = load_chunks(CHUNKS_PATH)
    print(f"{len(chunks)} chunks chargés depuis {CHUNKS_PATH}")
 
    co = cohere.Client(cohere_api_key)
    qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
 
    create_collection_if_not_exists(qdrant)
 
    # Cohere accepte des batchs de textes en un seul appel API (plus efficace
    # que d'appeler l'API une fois par chunk)
    BATCH_SIZE = 96  # limite raisonnable par appel Cohere
    points = []
 
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        texts = [c["text"] for c in batch]
 
        print(f"Génération des embeddings pour les chunks {i} à {i + len(batch)}...")
        embeddings = get_embeddings(co, texts)
 
        for chunk, vector in zip(batch, embeddings):
            points.append(
                PointStruct(
                    id=i + batch.index(chunk),  # id numérique unique
                    vector=vector,
                    payload={
                        "chunk_id": chunk["chunk_id"],
                        "section_id": chunk["section_id"],
                        "title": chunk["title"],
                        "text": chunk["text"],  # texte brut, indispensable pour BM25/rerank
                    },
                )
            )
 
    qdrant.upsert(collection_name=QDRANT_COLLECTION_NAME, points=points)
    print(f"\n{len(points)} points insérés dans Qdrant (collection '{QDRANT_COLLECTION_NAME}').")
 
    # Vérification rapide : compte les points dans la collection
    count = qdrant.count(collection_name=QDRANT_COLLECTION_NAME).count
    print(f"Vérification : {count} points présents dans la collection.")
 
 
if __name__ == "__main__":
    main()
 