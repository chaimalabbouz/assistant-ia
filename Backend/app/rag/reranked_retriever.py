"""
Retriever hybride + reranking (version asynchrone) : recupere un pool de
candidats via BM25 et embeddings (union, sans fusion par rang), puis les
rescore avec Cohere Rerank (cross-encoder) pour obtenir le classement final.

Usage (en import):
    from ingestion.reranked_retriever import RerankedRetriever

    retriever = RerankedRetriever()
    results = await retriever.search("How many sick days do I get?", top_k=5)
    ...
    await retriever.close()
"""

import asyncio
import json
import os
import re
import sys
from functools import lru_cache
from pathlib import Path

import cohere
from dotenv import load_dotenv
from nltk.stem.snowball import SnowballStemmer
from qdrant_client import AsyncQdrantClient
from rank_bm25 import BM25Okapi

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import CHUNKS_PATH, QDRANT_HOST, QDRANT_PORT, QDRANT_COLLECTION_NAME

load_dotenv()

EMBED_MODEL = "embed-english-v3.0"
RERANK_MODEL = "rerank-english-v3.0"

# --- Timeout / retry ---
REQUEST_TIMEOUT = 10.0   # secondes, par tentative
MAX_RETRIES = 3          # nombre total de tentatives
BACKOFF_BASE = 1.0       # attente entre tentatives : 1s, 2s, 4s...

# --- BM25 : stemming + stopwords ---
_stemmer = SnowballStemmer("english")
STOPWORDS = frozenset(_stemmer.stopwords)  # liste anglaise integree a nltk, sans telechargement


@lru_cache(maxsize=50_000)
def _stem(word: str) -> str:
    return _stemmer.stem(word)


def tokenize(text: str) -> list[str]:
    """Minuscules -> mots alphanumeriques -> retrait des stopwords -> stemming."""
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [_stem(w) for w in words if w not in STOPWORDS]


class RerankedRetriever:
    def __init__(self):
        cohere_api_key = os.getenv("COHERE_API_KEY")
        if not cohere_api_key:
            raise ValueError("COHERE_API_KEY introuvable dans .env")

        self.co = cohere.AsyncClient(cohere_api_key, timeout=REQUEST_TIMEOUT)
        self.qdrant = AsyncQdrantClient(
            host=QDRANT_HOST, port=QDRANT_PORT, timeout=int(REQUEST_TIMEOUT)
        )

        self.chunks = self._load_chunks(CHUNKS_PATH)
        tokenized_corpus = [tokenize(c["text"]) for c in self.chunks]
        self.bm25 = BM25Okapi(tokenized_corpus)

        print(f"RerankedRetriever initialise : {len(self.chunks)} chunks indexes.")

    @staticmethod
    def _load_chunks(path: Path) -> list[dict]:
        chunks = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                chunks.append(json.loads(line))
        return chunks

    async def close(self):
        """A appeler a l'arret de l'application pour fermer les connexions."""
        await self.qdrant.close()

    @staticmethod
    async def _with_retry(fn, *args, **kwargs):
        """Execute `fn` avec timeout par tentative et retry a backoff exponentiel."""
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                return await asyncio.wait_for(fn(*args, **kwargs), timeout=REQUEST_TIMEOUT)
            except Exception as e:
                if attempt == MAX_RETRIES:
                    raise
                delay = BACKOFF_BASE * 2 ** (attempt - 1)
                print(
                    f"[retry] {getattr(fn, '__name__', 'appel')} a echoue "
                    f"({type(e).__name__}), tentative {attempt}/{MAX_RETRIES}, "
                    f"nouvel essai dans {delay:.0f}s"
                )
                await asyncio.sleep(delay)

    def _bm25_search_sync(self, query: str, top_k: int) -> list[dict]:
        tokenized_query = tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)
        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        return [self.chunks[i] for i in ranked_indices]

    async def _bm25_search(self, query: str, top_k: int) -> list[dict]:
        # Calcul CPU : execute dans un thread pour ne pas bloquer la boucle asyncio
        return await asyncio.to_thread(self._bm25_search_sync, query, top_k)

    async def _dense_search(self, query: str, top_k: int) -> list[dict]:
        embedding_response = await self._with_retry(
            self.co.embed,
            texts=[query],
            model=EMBED_MODEL,
            input_type="search_query",
        )
        query_vector = embedding_response.embeddings[0]

        results = await self._with_retry(
            self.qdrant.search,
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
            }
            for r in results
        ]

    async def _get_candidate_pool(self, query: str, candidate_pool: int) -> list[dict]:
        """Union des candidats BM25 + dense (en parallele), dedupliques par chunk_id."""
        bm25_results, dense_results = await asyncio.gather(
            self._bm25_search(query, top_k=candidate_pool),
            self._dense_search(query, top_k=candidate_pool),
        )

        seen = {}
        for chunk in bm25_results + dense_results:
            seen[chunk["chunk_id"]] = chunk
        return list(seen.values())

    async def search(self, query: str, top_k: int = 5, candidate_pool: int = 20) -> list[dict]:
        """
        1) Recupere le pool de candidats (BM25 union dense), en parallele.
        2) Envoie ce pool a Cohere Rerank pour un rescoring precis.
        3) Retourne le top_k final selon le score de rerank.
        """
        candidates = await self._get_candidate_pool(query, candidate_pool)

        if not candidates:
            return []

        rerank_response = await self._with_retry(
            self.co.rerank,
            model=RERANK_MODEL,
            query=query,
            documents=[c["text"] for c in candidates],
            top_n=min(top_k, len(candidates)),
        )

        results = []
        for hit in rerank_response.results:
            chunk = candidates[hit.index]
            results.append(
                {
                    "chunk_id": chunk["chunk_id"],
                    "section_id": chunk["section_id"],
                    "title": chunk["title"],
                    "text": chunk["text"],
                    "rerank_score": hit.relevance_score,
                }
            )
        return results