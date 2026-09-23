"""
Evalue le retriever (embeddings seuls, pour l'instant) sur le golden
dataset : pour chaque question, verifie si le bon section_id apparait
dans les resultats, et calcule Recall@K et MRR.

Usage:
    python -m eval.run_retrieval_eval
"""

import json
import os
import sys
from pathlib import Path

import cohere
from dotenv import load_dotenv
from qdrant_client import QdrantClient

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import QDRANT_HOST, QDRANT_PORT, QDRANT_COLLECTION_NAME, GOLDEN_DATASET_PATH

load_dotenv()

COHERE_MODEL = "embed-english-v3.0"
TOP_K = 5


def load_golden_dataset(path: Path) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def search(co_client, qdrant_client, question: str, top_k: int = TOP_K):
    embedding_response = co_client.embed(
        texts=[question],
        model=COHERE_MODEL,
        input_type="search_query",
    )
    query_vector = embedding_response.embeddings[0]

    results = qdrant_client.search(
        collection_name=QDRANT_COLLECTION_NAME,
        query_vector=query_vector,
        limit=top_k,
    )
    return [r.payload["section_id"] for r in results]


def evaluate_one(retrieved_ids: list[str], expected_id: str) -> dict:
    """
    Retourne si le bon id a ete trouve (hit) et a quel rang (pour le MRR).
    """
    for rank, sid in enumerate(retrieved_ids, start=1):
        if sid == expected_id:
            return {"hit": True, "rank": rank, "reciprocal_rank": 1 / rank}
    return {"hit": False, "rank": None, "reciprocal_rank": 0}


def main():
    cohere_api_key = os.getenv("COHERE_API_KEY")
    co = cohere.Client(cohere_api_key)
    qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    dataset = load_golden_dataset(GOLDEN_DATASET_PATH)
    print(f"{len(dataset)} questions chargees depuis le golden dataset.\n")

    results = []
    for item in dataset:
        question = item["question"]
        expected_id = item["expected_section_id"]

        retrieved_ids = search(co, qdrant, question, top_k=TOP_K)
        eval_result = evaluate_one(retrieved_ids, expected_id)

        results.append(
            {
                "question": question,
                "expected_section_id": expected_id,
                "retrieved_section_ids": retrieved_ids,
                **eval_result,
            }
        )

        status = "OK" if eval_result["hit"] else "MISS"
        rank_info = f"rank={eval_result['rank']}" if eval_result["hit"] else "not found"
        print(f"[{status}] ({rank_info}) {question[:70]}")

    # --- Metriques globales ---
    n = len(results)
    hits = sum(1 for r in results if r["hit"])
    recall_at_k = hits / n
    mrr = sum(r["reciprocal_rank"] for r in results) / n

    print("\n" + "=" * 70)
    print("RESULTATS GLOBAUX (embeddings seuls, baseline)")
    print("=" * 70)
    print(f"Questions evaluees : {n}")
    print(f"Recall@{TOP_K} : {recall_at_k:.2%} ({hits}/{n})")
    print(f"MRR : {mrr:.4f}")

    # Sauvegarde des resultats detailles pour comparaison future
    EVAL_RESULTS_DIR = GOLDEN_DATASET_PATH.parent.parent / "results"
    EVAL_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = EVAL_RESULTS_DIR / "embeddings_only_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "config": "embeddings_only",
                "top_k": TOP_K,
                "recall_at_k": recall_at_k,
                "mrr": mrr,
                "details": results,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )
    print(f"\nResultats detailles sauvegardes dans {output_path}")

    # Affiche les questions ratees pour analyse
    misses = [r for r in results if not r["hit"]]
    if misses:
        print(f"\n--- {len(misses)} questions ratees ---")
        for m in misses:
            print(f"  Q: {m['question']}")
            print(f"     Attendu: {m['expected_section_id']} | Trouve: {m['retrieved_section_ids']}")


if __name__ == "__main__":
    main()
