"""
Evalue le retriever HYBRIDE + RERANKED sur le meme golden dataset,
avec comparaison aux deux configs precedentes (embeddings seuls, hybrid RRF).

Usage:
    python -m eval.run_reranked_eval
"""

import json
import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import GOLDEN_DATASET_PATH
from rag.reranked_retriever import RerankedRetriever

TOP_K = 5
DELAY_BETWEEN_QUESTIONS = 7  # secosndes, pour respecter le rate limit Cohere Trial (10 appels/min)


def load_golden_dataset(path: Path) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def evaluate_one(retrieved_ids: list[str], expected_id: str) -> dict:
    for rank, sid in enumerate(retrieved_ids, start=1):
        if sid == expected_id:
            return {"hit": True, "rank": rank, "reciprocal_rank": 1 / rank}
    return {"hit": False, "rank": None, "reciprocal_rank": 0}


def main():
    retriever = RerankedRetriever()

    dataset = load_golden_dataset(GOLDEN_DATASET_PATH)
    print(f"\n{len(dataset)} questions chargees depuis le golden dataset.\n")

    results = []
    for item in dataset:
        question = item["question"]
        expected_id = item["expected_section_id"]

        retrieved = retriever.search(question, top_k=TOP_K)
        retrieved_ids = [r["section_id"] for r in retrieved]
        eval_result = evaluate_one(retrieved_ids, expected_id)
        time.sleep(DELAY_BETWEEN_QUESTIONS)

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

    n = len(results)
    hits = sum(1 for r in results if r["hit"])
    recall_at_k = hits / n
    mrr = sum(r["reciprocal_rank"] for r in results) / n

    print("\n" + "=" * 70)
    print("RESULTATS GLOBAUX (hybrid + Cohere rerank)")
    print("=" * 70)
    print(f"Questions evaluees : {n}")
    print(f"Recall@{TOP_K} : {recall_at_k:.2%} ({hits}/{n})")
    print(f"MRR : {mrr:.4f}")

    EVAL_RESULTS_DIR = GOLDEN_DATASET_PATH.parent.parent / "results"
    EVAL_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = EVAL_RESULTS_DIR / "reranked_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "config": "hybrid_reranked",
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

    misses = [r for r in results if not r["hit"]]
    if misses:
        print(f"\n--- {len(misses)} questions ratees ---")
        for m in misses:
            print(f"  Q: {m['question']}")
            print(f"     Attendu: {m['expected_section_id']} | Trouve: {m['retrieved_section_ids']}")

    # --- Comparaison avec les configs precedentes ---
    print("\n" + "=" * 70)
    print("COMPARAISON")
    print("=" * 70)
    print(f"{'Config':<30} {'Recall@5':<12} {'MRR':<8}")

    for name, fname in [
        ("Embeddings seuls", "embeddings_only_results.json"),
        ("Hybrid (RRF)", "hybrid_results.json"),
    ]:
        path = EVAL_RESULTS_DIR / fname
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                prev = json.load(f)
            print(f"{name:<30} {prev['recall_at_k']:.2%}      {prev['mrr']:.4f}")

    print(f"{'Hybrid + rerank':<30} {recall_at_k:.2%}      {mrr:.4f}")


if __name__ == "__main__":
    main()