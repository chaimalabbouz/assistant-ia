"""
Retriever hybride : BM25 (mots-cles exacts) + embeddings Cohere (semantique),
fusionnes via Reciprocal Rank Fusion (RRF).
 
BM25 tourne entierement en local (pas d'appel API) sur le texte de tous les
chunks. Les embeddings passent par Cohere + Qdrant comme avant.
 
Usage (en import):
    from ingestion.hybrid_retriever import HybridRetriever
    retriever = HybridRetriever()
    results = retriever.search("How many sick days do I get?", top_k=5)
"""
 
import json
import os
import re
import sys
from pathlib import Path
 
import cohere
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from rank_bm25 import BM25Okapi
 
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import CHUNKS_PATH, QDRANT_HOST, QDRANT_PORT, QDRANT_COLLECTION_NAME
 
load_dotenv()
 
COHERE_MODEL = "embed-english-v3.0"
RRF_K = 60  # constante standard du Reciprocal Rank Fusion
 
 
def tokenize(text: str) -> list[str]:
    """Tokenisation simple : minuscules, mots alphanumeriques uniquement."""
    return re.findall(r"[a-z0-9]+", text.lower())
 
 
class HybridRetriever:
    def __init__(self):
        cohere_api_key = os.getenv("COHERE_API_KEY")
        if not cohere_api_key:
            raise ValueError("COHERE_API_KEY introuvable dans .env")
 
        self.co = cohere.Client(cohere_api_key)
        self.qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
 
        # Charge tous les chunks pour construire l'index BM25 (local, pas d'API)
        self.chunks = self._load_chunks(CHUNKS_PATH)
        tokenized_corpus = [tokenize(c["text"]) for c in self.chunks]
        self.bm25 = BM25Okapi(tokenized_corpus)
 
        print(f"HybridRetriever initialise : {len(self.chunks)} chunks indexes (BM25 + Qdrant).")
 
    @staticmethod
    def _load_chunks(path: Path) -> list[dict]:
        chunks = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                chunks.append(json.loads(line))
        return chunks
 
    def _bm25_search(self, query: str, top_k: int) -> list[dict]:
        """Retourne les top_k chunks selon BM25, avec leur rang."""
        tokenized_query = tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)
 
        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
 
        return [
            {**self.chunks[i], "bm25_score": float(scores[i])}
            for i in ranked_indices
        ]
 
    def _dense_search(self, query: str, top_k: int) -> list[dict]:
        """Retourne les top_k chunks selon la similarite d'embeddings (Qdrant)."""
        embedding_response = self.co.embed(
            texts=[query],
            model=COHERE_MODEL,
            input_type="search_query",
        )
        query_vector = embedding_response.embeddings[0]
 
        results = self.qdrant.search(
            collection_name=QDRANT_COLLECTION_NAME,
            query_vector=query_vector,
            limit=top_k,
        )
 
        return [
            {
                "chunk_id": r.payload["chunk_id"],
                "section_id": r.payload["section_id"],
                "title": r.payload["title"],
                "text": r.payload["text"],
                "dense_score": r.score,
            }
            for r in results
        ]
 
    def search(self, query: str, top_k: int = 5, candidate_pool: int = 20) -> list[dict]:
        """
        Recherche hybride : recupere candidate_pool resultats de chaque
        systeme (BM25 + dense), fusionne via RRF, retourne le top_k final.
        """
        bm25_results = self._bm25_search(query, top_k=candidate_pool)
        dense_results = self._dense_search(query, top_k=candidate_pool)
 
        # Calcule le score RRF pour chaque chunk_id vu par au moins un systeme
        rrf_scores: dict[str, float] = {}
        chunk_lookup: dict[str, dict] = {}
 
        for rank, chunk in enumerate(bm25_results, start=1):
            cid = chunk["chunk_id"]
            rrf_scores[cid] = rrf_scores.get(cid, 0) + 1 / (RRF_K + rank)
            chunk_lookup[cid] = chunk
 
        for rank, chunk in enumerate(dense_results, start=1):
            cid = chunk["chunk_id"]
            rrf_scores[cid] = rrf_scores.get(cid, 0) + 1 / (RRF_K + rank)
            chunk_lookup[cid] = chunk
 
        # Trie par score RRF decroissant, garde le top_k final
        sorted_ids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)[:top_k]
 
        return [
            {
                "chunk_id": cid,
                "section_id": chunk_lookup[cid]["section_id"],
                "title": chunk_lookup[cid]["title"],
                "text": chunk_lookup[cid]["text"],
                "rrf_score": rrf_scores[cid],
            }
            for cid in sorted_ids
        ]
 
 
if __name__ == "__main__":
    # Test rapide manuel
    retriever = HybridRetriever()
    test_questions = [
        "How many sick days do employees get?",
        "What is the difference between vacation and PTO?",
        "Can I use sick leave to go vote if the polls aren't open outside my work hours?",
    ]
    for q in test_questions:
        print(f"\n{'=' * 70}\nQUESTION: {q}\n{'=' * 70}")
        results = retriever.search(q, top_k=5)
        for rank, r in enumerate(results, start=1):
            preview = r["text"][:100].replace("\n", " ")
            print(f"  #{rank} | rrf={r['rrf_score']:.4f} | [{r['section_id']}] {r['title']}")
            print(f"       {preview}...")
 