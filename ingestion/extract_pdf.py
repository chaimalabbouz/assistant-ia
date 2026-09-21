"""
Extraction et structuration du texte du
Clark County Human Resources Policy Manual.

Entrée :
    RAW_PDF_PATH défini dans config.py

Sortie :
    RAW_SECTIONS_PATH défini dans config.py

Structure :

[
    {
        "section_id": "3.0",
        "title": "Equal Opportunity Employment and Harassment",
        "content": "...",
        "subsections": [
            {
                "section_id": "3.1",
                "title": "EQUAL OPPORTUNITY AND NON-DISCRIMINATION",
                "content": "..."
            },
            {
                "section_id": "3.2",
                "title": "WORKPLACE HARASSMENT",
                "content": "..."
            },
            {
                "section_id": "3.3",
                "title": "COMPLAINT PROCESS",
                "content": "..."
            }
        ]
    }
]
"""

import sys
import json
import re
from pathlib import Path

import fitz


# ============================================================
# CONFIG
# ============================================================

# Permet d'importer config.py depuis la racine du projet
sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import RAW_PDF_PATH, RAW_SECTIONS_PATH


# ============================================================
# REGEX
# ============================================================

# Exemple :
# Policy No. 3.0
# Policy No. 11.0
POLICY_MARKER_RE = re.compile(
    r"^\s*Policy No\.\s*(\d+\.0)\s*$",
    re.IGNORECASE,
)

# Sous-sections :
#
# 3.1 EQUAL OPPORTUNITY...
# 3.2 WORKPLACE HARASSMENT
# 3.3 COMPLAINT PROCESS
# 11.1A ...
# 11.1B ...
#
SUBSECTION_RE = re.compile(
    r"^\s*(\d+\.\d+[A-Z]?)\s{1,}(.+?)\s*$"
)

# Page X of Y
PAGE_RE = re.compile(
    r"^\s*Page\s+\d+\s+of\s+\d+\s*$",
    re.IGNORECASE,
)

# Chemin présent dans le document
PATH_RE = re.compile(
    r"^\s*K:\\COUNTY\\HRCOUNTY\\HR Policy Manual\\.*$",
    re.IGNORECASE,
)


# ============================================================
# TEXT CLEANING
# ============================================================

def normalize_line(line: str) -> str:
    """
    Nettoie une ligne extraite du PDF.
    """

    line = line.replace("\xa0", " ")

    # Plusieurs espaces -> un espace
    line = re.sub(r"[ \t]+", " ", line)

    return line.strip()


def normalize_text(text: str) -> str:
    """
    Nettoie le texte final sans supprimer sa structure.
    """

    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")
    text = text.replace("\xa0", " ")

    text = re.sub(r"[ \t]+", " ", text)

    # Maximum une ligne vide entre deux blocs
    text = re.sub(
        r"\n[ \t]*\n+",
        "\n\n",
        text,
    )

    return text.strip()


def clean_page_lines(text: str) -> list[str]:
    """
    Transforme le texte brut d'une page en lignes propres.
    """

    lines = []

    for raw_line in text.splitlines():

        line = normalize_line(raw_line)

        if line:
            lines.append(line)

    return lines


# ============================================================
# PDF EXTRACTION
# ============================================================

def extract_pages(pdf_path: Path) -> list[list[str]]:
    """
    Extrait le texte page par page.
    """

    doc = fitz.open(pdf_path)

    pages = []

    try:

        for page in doc:

            text = page.get_text("text")

            lines = clean_page_lines(text)

            pages.append(lines)

    finally:

        doc.close()

    return pages


# ============================================================
# TABLE OF CONTENTS
# ============================================================

def is_table_of_contents_page(
    lines: list[str],
) -> bool:
    """
    Détecte les pages de table des matières.
    """

    text = "\n".join(lines).lower()

    return (
        "table of contents" in text
        or "table of content" in text
    )


def find_first_policy_page(
    pages: list[list[str]],
) -> int:
    """
    Trouve la première vraie page de policy.

    On ignore les pages de table des matières.
    """

    for page_index, lines in enumerate(pages):

        if is_table_of_contents_page(lines):
            continue

        for line in lines:

            if POLICY_MARKER_RE.match(line):
                return page_index

    raise ValueError(
        "Aucune vraie policy n'a été trouvée."
    )


# ============================================================
# POLICY DETECTION
# ============================================================

def find_policy_marker(
    lines: list[str],
) -> tuple[int, str] | None:
    """
    Cherche Policy No. X.0 dans une page.

    Retourne :
        (index de la ligne, policy_id)

    Exemple :
        (2, "3.0")
    """

    for index, line in enumerate(lines):

        match = POLICY_MARKER_RE.match(line)

        if match:
            return index, match.group(1)

    return None


def extract_policy_title(
    lines: list[str],
    policy_index: int,
) -> str:
    """
    Extrait le titre de la policy.

    Exemple :

        Policy No. 3.0
        Equal Opportunity Employment
        and Harassment
        Page 1 of 6

    devient :

        Equal Opportunity Employment and Harassment
    """

    title_parts = []

    for line in lines[policy_index + 1:]:

        # Fin du titre
        if PAGE_RE.match(line):
            break

        if line == "Policy Sections:":
            break

        if line == "Effective:":
            break

        if line == "Supersedes:":
            break

        if PATH_RE.match(line):
            break

        if POLICY_MARKER_RE.match(line):
            break

        title_parts.append(line)

    return " ".join(title_parts).strip()


# ============================================================
# PAGE METADATA
# ============================================================

def remove_page_metadata(
    lines: list[str],
) -> list[str]:
    """
    Supprime les headers/footers répétitifs.

    IMPORTANT :
    Policy No. X.0 est conservé ici car il permet
    d'identifier la policy de la page.
    """

    cleaned = []

    for line in lines:

        # Page 1 of 6
        if PAGE_RE.match(line):
            continue

        # Chemin Windows
        if PATH_RE.match(line):
            continue

        # Header
        if line.lower() == "human resources policy manual":
            continue

        # Metadata
        if line in {
            "Policy Sections:",
            "Effective:",
            "Supersedes:",
        }:
            continue

        cleaned.append(line)

    return cleaned


# ============================================================
# SUBSECTION
# ============================================================

def parse_subsection_marker(
    line: str,
) -> tuple[str, str] | None:
    """
    Détecte une vraie sous-section.

    Accepte :

        3.1 ...
        3.2 ...
        3.3 ...
        11.1A ...
        11.1B ...

    N'accepte pas :

        3.0
        4.0
    """

    match = SUBSECTION_RE.match(line)

    if not match:
        return None

    section_id = match.group(1)
    title = match.group(2).strip()

    # X.0 = policy principale
    if re.fullmatch(
        r"\d+\.0",
        section_id,
    ):
        return None

    if not title:
        return None

    return section_id, title


# ============================================================
# BUILD SUBSECTIONS
# ============================================================

def build_subsections(
    lines: list[str],
) -> tuple[str, list[dict]]:
    """
    Sépare :

        contenu principal
        sous-sections

    Le contenu avant la première sous-section reste
    dans "content".

    Cela permet de conserver :

        PURPOSE
        SCOPE

    dans le contenu de la policy principale.
    """

    main_content = []

    subsections = []

    current_subsection = None

    for line in lines:

        marker = parse_subsection_marker(line)

        # ----------------------------------------------------
        # Nouvelle sous-section
        # ----------------------------------------------------

        if marker:

            # Sauvegarder la sous-section précédente
            if current_subsection is not None:

                content = normalize_text(
                    "\n".join(
                        current_subsection["content"]
                    )
                )

                if content:

                    current_subsection["content"] = content

                    subsections.append(
                        current_subsection
                    )

            section_id, title = marker

            current_subsection = {
                "section_id": section_id,
                "title": title,
                "content": [],
            }

            continue

        # ----------------------------------------------------
        # Contenu de la sous-section
        # ----------------------------------------------------

        if current_subsection is not None:

            current_subsection["content"].append(
                line
            )

        # ----------------------------------------------------
        # Contenu avant la première sous-section
        #
        # Exemple :
        # PURPOSE
        # ...
        # SCOPE
        # ...
        # ----------------------------------------------------

        else:

            main_content.append(line)

    # --------------------------------------------------------
    # Dernière sous-section
    # --------------------------------------------------------

    if current_subsection is not None:

        content = normalize_text(
            "\n".join(
                current_subsection["content"]
            )
        )

        if content:

            current_subsection["content"] = content

            subsections.append(
                current_subsection
            )

    return (
        normalize_text(
            "\n".join(main_content)
        ),
        subsections,
    )


# ============================================================
# CLEAN POLICY CONTENT
# ============================================================

def clean_policy_page(lines: list[str]) -> list[str]:
    """
    Supprime tout le bloc d'en-tête de la policy.

    Exemple supprimé :

        Policy No. 3.0
        Equal Opportunity Employment and Harassment
        Page 1 of 6
        Policy Sections:
        3.1 ...
        3.2 ...
        3.3 ...
        Effective:
        09/22/2009
        Supersedes:
        04/18/2005
        K:\\COUNTY\\HRCOUNTY\\HR Policy Manual\\...

    Le vrai contenu commence après le chemin K:\\...
    """

    # --------------------------------------------------------
    # Chercher le chemin qui termine le bloc metadata
    # --------------------------------------------------------

    path_index = None

    for i, line in enumerate(lines):

        if PATH_RE.match(line):
            path_index = i
            break

    # --------------------------------------------------------
    # Si le chemin existe :
    # tout ce qui est AVANT est du header.
    # On garde uniquement le contenu après le chemin.
    # --------------------------------------------------------

    if path_index is not None:

        lines = lines[path_index + 1:]

    # --------------------------------------------------------
    # Nettoyage supplémentaire
    # --------------------------------------------------------

    cleaned = []

    for line in lines:

        # Au cas où un header apparaît encore
        if POLICY_MARKER_RE.match(line):
            continue

        if PAGE_RE.match(line):
            continue

        if line.lower() == "human resources policy manual":
            continue

        cleaned.append(line)

    return cleaned


# ============================================================
# REMOVE REPEATED TITLE
# ============================================================

def remove_repeated_header_title(
    lines: list[str],
    title: str,
) -> list[str]:
    """
    Supprime le titre répété dans les headers.

    Exemple :

        Equal Opportunity Employment and
        Harassment

    """

    if not title:
        return lines

    title_normalized = normalize_text(
        title
    ).lower()

    result = []

    i = 0

    while i < len(lines):

        found = False

        # Le titre peut être sur plusieurs lignes.
        for count in range(1, 4):

            if i + count > len(lines):
                break

            candidate = normalize_text(
                " ".join(
                    lines[i:i + count]
                )
            ).lower()

            if candidate == title_normalized:

                # Un titre de header apparaît au début
                # de la page.
                if i < 4:

                    i += count
                    found = True
                    break

        if found:
            continue

        result.append(lines[i])

        i += 1

    return result


# ============================================================
# FINALIZE ONE POLICY
# ============================================================

def finalize_policy(
    policy: dict,
) -> dict:
    """
    Construit UN SEUL objet pour une policy complète,
    même si elle occupe plusieurs pages.
    """

    all_lines = []

    # Toutes les pages de la même policy
    for page_lines in policy["pages"]:

        cleaned = clean_policy_page(
            page_lines
        )

        all_lines.extend(cleaned)

    # Nettoyage du titre répété
    all_lines = remove_repeated_header_title(
        all_lines,
        policy["title"],
    )

    # Construire contenu + sous-sections
    content, subsections = build_subsections(
        all_lines
    )

    return {
        "section_id": policy["section_id"],
        "title": policy["title"],
        "content": content,
        "subsections": subsections,
    }


# ============================================================
# EXTRACT POLICIES
# ============================================================

def extract_policies(
    pages: list[list[str]],
) -> list[dict]:
    """
    Extrait les policies.

    IMPORTANT :
    La présence de "Policy No. 3.0" sur une page NE crée
    PAS automatiquement une nouvelle policy.

    Une nouvelle policy est créée UNIQUEMENT lorsque le
    numéro change :

        1.0 -> 2.0
        2.0 -> 3.0
        3.0 -> 4.0
        etc.
    """

    first_policy_page = find_first_policy_page(
        pages
    )

    policies = []

    current_policy = None
    current_policy_id = None

    # Commencer à la première vraie policy
    for page_index in range(
        first_policy_page,
        len(pages),
    ):

        page_lines = pages[page_index]

        marker = find_policy_marker(
            page_lines
        )

        # ====================================================
        # PAGE AVEC "Policy No. X.0"
        # ====================================================

        if marker is not None:

            marker_index, detected_policy_id = marker

            # ------------------------------------------------
            # CAS 1 :
            # première policy
            # ------------------------------------------------

            if current_policy is None:

                title = extract_policy_title(
                    page_lines,
                    marker_index,
                )

                current_policy_id = (
                    detected_policy_id
                )

                current_policy = {
                    "section_id": current_policy_id,
                    "title": title,
                    "pages": [],
                }

            # ------------------------------------------------
            # CAS 2 :
            # même policy
            #
            # Exemple :
            #
            # page 16 -> Policy No. 3.0
            # page 17 -> Policy No. 3.0
            # page 18 -> Policy No. 3.0
            #
            # On ajoute simplement la page.
            # ------------------------------------------------

            elif detected_policy_id == current_policy_id:

                pass

            # ------------------------------------------------
            # CAS 3 :
            # NOUVELLE policy
            #
            # Exemple :
            #
            # page précédente -> 3.0
            # nouvelle page   -> 4.0
            # ------------------------------------------------

            else:

                # Sauvegarder l'ancienne
                policies.append(
                    finalize_policy(
                        current_policy
                    )
                )

                # Créer la nouvelle
                title = extract_policy_title(
                    page_lines,
                    marker_index,
                )

                current_policy_id = (
                    detected_policy_id
                )

                current_policy = {
                    "section_id": current_policy_id,
                    "title": title,
                    "pages": [],
                }

        # ====================================================
        # AJOUTER LA PAGE À LA POLICY COURANTE
        # ====================================================

        if current_policy is not None:

            current_policy["pages"].append(
                page_lines
            )

    # ========================================================
    # DERNIÈRE POLICY
    # ========================================================

    if current_policy is not None:

        policies.append(
            finalize_policy(
                current_policy
            )
        )

    return policies


# ============================================================
# VALIDATION
# ============================================================

def validate_policies(
    policies: list[dict],
) -> None:
    """
    Vérifie que chaque policy apparaît une seule fois.
    """

    print("\n" + "=" * 70)
    print("VALIDATION")
    print("=" * 70)

    print(
        f"\nNombre de policies détectées : "
        f"{len(policies)}"
    )

    # --------------------------------------------------------
    # IDs
    # --------------------------------------------------------

    ids = [
        policy["section_id"]
        for policy in policies
    ]

    duplicates = sorted(
        {
            section_id
            for section_id in ids
            if ids.count(section_id) > 1
        }
    )

    if duplicates:

        print(
            "\n⚠ IDs de policies dupliqués :"
        )

        for duplicate in duplicates:
            print(
                f"   - {duplicate}"
            )

    else:

        print(
            "\n✓ Aucun ID de policy dupliqué."
        )

    # --------------------------------------------------------
    # Aperçu
    # --------------------------------------------------------

    print("\nPremières policies :")

    for policy in policies[:10]:

        print(
            f"  [{policy['section_id']}] "
            f"{policy['title']}"
        )

        print(
            f"      Sous-sections : "
            f"{len(policy['subsections'])}"
        )

        for subsection in policy[
            "subsections"
        ][:5]:

            print(
                f"        └─ "
                f"[{subsection['section_id']}] "
                f"{subsection['title']}"
            )


# ============================================================
# SAVE
# ============================================================

def save_json(
    policies: list[dict],
    output_path: Path,
) -> None:
    """
    Sauvegarde le JSON final.
    """

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            policies,
            file,
            indent=2,
            ensure_ascii=False,
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("CLARK COUNTY HR POLICY MANUAL")
    print("Extraction du texte")
    print("=" * 70)

    # --------------------------------------------------------
    # Vérification PDF
    # --------------------------------------------------------

    if not RAW_PDF_PATH.exists():

        raise FileNotFoundError(
            f"PDF introuvable : "
            f"{RAW_PDF_PATH}"
        )

    print(
        f"\nLecture du PDF : "
        f"{RAW_PDF_PATH}"
    )

    # --------------------------------------------------------
    # Extraction
    # --------------------------------------------------------

    pages = extract_pages(
        RAW_PDF_PATH
    )

    print(
        f"Nombre de pages extraites : "
        f"{len(pages)}"
    )

    # --------------------------------------------------------
    # Parsing
    # --------------------------------------------------------

    print(
        "\nDétection et structuration "
        "des policies..."
    )

    policies = extract_policies(
        pages
    )

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    validate_policies(
        policies
    )

    # --------------------------------------------------------
    # Sauvegarde
    # --------------------------------------------------------

    save_json(
        policies,
        RAW_SECTIONS_PATH
    )

    print(
        f"\n✓ Extraction terminée."
    )

    print(
        f"✓ Fichier sauvegardé dans : "
        f"{RAW_SECTIONS_PATH}"
    )

    # --------------------------------------------------------
    # Aperçu détaillé de 3.0
    # --------------------------------------------------------

    policy_3 = next(
        (
            policy
            for policy in policies
            if policy["section_id"] == "3.0"
        ),
        None,
    )

    if policy_3 is not None:

        print(
            "\n" + "=" * 70
        )

        print(
            "APERÇU DE LA POLICY 3.0"
        )

        print("=" * 70)

        print(
            f"\nID : {policy_3['section_id']}"
        )

        print(
            f"Titre : {policy_3['title']}"
        )

        print(
            f"\nNombre de sous-sections : "
            f"{len(policy_3['subsections'])}"
        )

        print("\nSous-sections :")

        for subsection in policy_3[
            "subsections"
        ]:

            print(
                f"  [{subsection['section_id']}] "
                f"{subsection['title']}"
            )

        print("\nContenu principal :")

        print(
            policy_3["content"][:500]
        )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()