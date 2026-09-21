"""
Extraction du texte du PDF Clark County HR Policy Manual.
Détecte les sections via le pattern "Policy No. X.0 <Titre>" qui apparaît
en en-tête de chaque section dans ce document.

Usage:
    python ingestion/extract_pdf.py
Produit:
    data/processed/raw_sections.json
"""

import json
import re
from pathlib import Path
from config import RAW_PDF_PATH, OUTPUT_PATH
import fitz  # PyMuPDF



# Repère une ligne de type "Policy No. 11.6 Sick Leave" ou "Policy No. 5.0 Recruitment..."
SECTION_HEADER_PATTERN = re.compile(
    r"Policy No\.\s*(\d+\.\d+[A-Z]?)\s+([A-Za-z][^\n]{0,80})"
)

# Lignes récurrentes de footer/header à supprimer (bruit répété sur chaque page)
NOISE_PATTERNS = [
    re.compile(r"K:\\COUNTY\\HRCOUNTY.*\.doc", re.IGNORECASE),
    re.compile(r"^CLARK COUNTY$", re.MULTILINE),
    re.compile(r"^HUMAN RESOURCES POLICY MANUAL$", re.MULTILINE),
    re.compile(r"^TABLE OF CONTENTS$", re.MULTILINE),
    re.compile(r"Page \d+ of \d+"),
]


def extract_raw_text(pdf_path: Path) -> str:
    """Extrait tout le texte brut du PDF, page par page."""
    doc = fitz.open(pdf_path)
    pages_text = []
    for page in doc:
        pages_text.append(page.get_text())
    doc.close()
    return "\n".join(pages_text)


def clean_text(text: str) -> str:
    """Supprime le bruit récurrent (headers/footers répétés)."""
    for pattern in NOISE_PATTERNS:
        text = pattern.sub("", text)
    # Normalise les espaces multiples et lignes vides répétées
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_into_sections(text: str) -> list[dict]:
    """
    Découpe le texte en sections basées sur les headers "Policy No. X.X Titre".
    Chaque section conserve son numéro, son titre, et son contenu jusqu'à la
    section suivante.
    """
    matches = list(SECTION_HEADER_PATTERN.finditer(text))
    sections = []

    for i, match in enumerate(matches):
        section_id = match.group(1).strip()
        title = match.group(2).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()

        # Ignore les matches vides ou trop courts (probablement des faux positifs
        # issus de la table des matières)
        if len(content) < 100:
            continue

        sections.append(
            {
                "section_id": section_id,
                "title": title,
                "content": content,
            }
        )

    return sections


def deduplicate_sections(sections: list[dict]) -> list[dict]:
    """
    Le même 'Policy No. X.X' peut apparaître plusieurs fois (une fois dans la
    table des matières, une fois en tête de section réelle). On garde la
    version avec le plus de contenu pour chaque section_id.
    """
    best_by_id: dict[str, dict] = {}
    for section in sections:
        sid = section["section_id"]
        if sid not in best_by_id or len(section["content"]) > len(
            best_by_id[sid]["content"]
        ):
            best_by_id[sid] = section
    # Garde l'ordre d'apparition original des IDs uniques
    seen = set()
    ordered = []
    for section in sections:
        sid = section["section_id"]
        if sid not in seen and best_by_id[sid] == section:
            ordered.append(section)
            seen.add(sid)
    return ordered


SUBSECTION_PATTERN = re.compile(
    r"\n(\d{1,2}\.\d{1,2}[A-Z]?)\s+([A-Z][A-Z0-9 /,\-'&]{3,70})\n"
)


def split_into_subsections(section: dict) -> list[dict]:
    """
    Redécoupe une section principale en sous-sections si des sous-titres
    (format '11.6 SICK LEAVE') sont détectés dans son contenu.
    Si aucune sous-section n'est trouvée, retourne la section telle quelle.
    """
    content = section["content"]
    matches = list(SUBSECTION_PATTERN.finditer(content))

    if not matches:
        return [section]

    subsections = []

    # Le texte avant le premier sous-titre reste rattaché à la section parente
    intro = content[: matches[0].start()].strip()
    if len(intro) > 100:
        subsections.append(
            {
                "section_id": section["section_id"],
                "title": section["title"],
                "content": intro,
            }
        )

    for i, match in enumerate(matches):
        sub_id = match.group(1).strip()
        sub_title = match.group(2).strip().title()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        sub_content = content[start:end].strip()

        if len(sub_content) < 80:
            continue

        subsections.append(
            {
                "section_id": sub_id,
                "title": sub_title,
                "content": sub_content,
            }
        )

    return subsections


def main():
    if not RAW_PDF_PATH.exists():
        raise FileNotFoundError(
            f"PDF introuvable à {RAW_PDF_PATH}. "
            f"Place le fichier téléchargé dans data/raw/ avant de lancer ce script."
        )

    print(f"Lecture de {RAW_PDF_PATH} ...")
    raw_text = extract_raw_text(RAW_PDF_PATH)
    print(f"{len(raw_text)} caractères extraits.")

    cleaned_text = clean_text(raw_text)

    sections = split_into_sections(cleaned_text)
    sections = deduplicate_sections(sections)
    print(f"{len(sections)} sections principales détectées.")

    all_subsections = []
    for section in sections:
        all_subsections.extend(split_into_subsections(section))
    sections = all_subsections
    print(f"{len(sections)} sections/sous-sections après découpage fin.")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(sections, f, indent=2, ensure_ascii=False)

    print(f"Sections sauvegardées dans {OUTPUT_PATH}")

    # Aperçu rapide pour vérification manuelle
    print("\n--- Aperçu des 5 premières sections ---")
    for s in sections[:5]:
        preview = s["content"][:120].replace("\n", " ")
        print(f"[{s['section_id']}] {s['title']} -> {preview}...")


if __name__ == "__main__":
    main()