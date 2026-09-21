"""
Découpe les policies/sous-sections extraites (raw_sections.json, structure
imbriquée avec "subsections") en chunks de taille contrôlée, prêts pour
l'embedding, via un découpage récursif (paragraphe > ligne > phrase > mot).

Chaque section ET chaque sous-section est chunkée indépendamment.

Usage:
    python -m ingestion.chunker
Produit:
    data/processed/chunks.jsonl
"""

import json
import sys
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import RAW_SECTIONS_PATH, CHUNKS_PATH

MAX_CHUNK_CHARS = 1200
CHUNK_OVERLAP = 150

splitter = RecursiveCharacterTextSplitter(
    chunk_size=MAX_CHUNK_CHARS,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", ". ", " ", ""],
)


def load_policies(path: Path) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def chunk_one_unit(section_id: str, title: str, content: str) -> list[dict]:
    """
    Découpe le texte d'une seule section/sous-section en un ou plusieurs
    chunks via le recursive splitter.
    """
    if not content or not content.strip():
        return []

    text_pieces = splitter.split_text(content)

    return [
        {
            "chunk_id": f"{section_id}::{i}",
            "section_id": section_id,
            "title": title,
            "text": piece,
        }
        for i, piece in enumerate(text_pieces)
        if piece.strip()
    ]


def chunk_policy(policy: dict) -> list[dict]:
    """
    Chunke une policy complète : son contenu principal (intro, PURPOSE/SCOPE
    avant la première sous-section) PUIS chacune de ses sous-sections.
    """
    chunks = []

    chunks.extend(
        chunk_one_unit(policy["section_id"], policy["title"], policy.get("content", ""))
    )

    for sub in policy.get("subsections", []):
        chunks.extend(
            chunk_one_unit(sub["section_id"], sub["title"], sub.get("content", ""))
        )

    return chunks


def main():
    if not RAW_SECTIONS_PATH.exists():
        raise FileNotFoundError(
            f"{RAW_SECTIONS_PATH} introuvable. Lance d'abord ingestion/extract_pdf.py."
        )

    policies = load_policies(RAW_SECTIONS_PATH)
    print(f"{len(policies)} policies chargées.")

    all_chunks = []
    for policy in policies:
        all_chunks.extend(chunk_policy(policy))

    print(f"{len(all_chunks)} chunks générés.")

    CHUNKS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
        for chunk in all_chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    print(f"Chunks sauvegardés dans {CHUNKS_PATH}")

    print("\n--- Aperçu de quelques chunks ---")
    for c in all_chunks[:5]:
        preview = c["text"][:100].replace("\n", " ")
        print(f"[{c['chunk_id']}] {c['title']} ({len(c['text'])} car.) -> {preview}...")

    sick_leave_chunks = [c for c in all_chunks if c["section_id"] == "11.6"]
    print(f"\nChunks trouvés pour 11.6 Sick Leave : {len(sick_leave_chunks)}")

    lengths = [len(c["text"]) for c in all_chunks]
    print(f"\nTaille moyenne des chunks: {sum(lengths)//len(lengths)} caractères")
    print(f"Taille min/max: {min(lengths)} / {max(lengths)} caractères")


if __name__ == "__main__":
    main()