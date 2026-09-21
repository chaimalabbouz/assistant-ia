"""
Découpe les sections/sous-sections extraites (raw_sections.json) en chunks
de taille contrôlée, prêts pour l'embedding, en utilisant un découpage
récursif (paragraphe > ligne > phrase > mot) pour ne jamais couper au
mauvais endroit.

Chaque section/sous-section est chunkée indépendamment : le chunking ne
fusionne jamais deux sections différentes, il respecte les frontières
déjà posées par extract_pdf.py.

Usage:
    python ingestion/chunker.py
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


def load_sections(path: Path) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def split_section_into_chunks(section: dict) -> list[dict]:
    content = section["content"]
    section_id = section["section_id"]
    title = section["title"]

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


def main():
    if not RAW_SECTIONS_PATH.exists():
        raise FileNotFoundError(
            f"{RAW_SECTIONS_PATH} introuvable. "
            f"Lance d'abord ingestion/extract_pdf.py."
        )

    sections = load_sections(RAW_SECTIONS_PATH)
    print(f"{len(sections)} sections chargées.")

    all_chunks = []
    for section in sections:
        all_chunks.extend(split_section_into_chunks(section))

    print(f"{len(all_chunks)} chunks générés.")

    CHUNKS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
        for chunk in all_chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    print(f"Chunks sauvegardés dans {CHUNKS_PATH}")

    print("\n--- Aperçu des 5 premiers chunks ---")
    for c in all_chunks[:5]:
        preview = c["text"][:100].replace("\n", " ")
        print(f"[{c['chunk_id']}] {c['title']} ({len(c['text'])} car.) -> {preview}...")

    lengths = [len(c["text"]) for c in all_chunks]
    print(f"\nTaille moyenne des chunks: {sum(lengths)//len(lengths)} caractères")
    print(f"Taille min/max: {min(lengths)} / {max(lengths)} caractères")


if __name__ == "__main__":
    main()