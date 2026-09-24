

import os
import sys
from pathlib import Path

import cohere
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_mistralai import ChatMistralAI
from qdrant_client import QdrantClient

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import QDRANT_HOST, QDRANT_PORT, QDRANT_COLLECTION_NAME

load_dotenv()

COHERE_MODEL = "embed-english-v3.0"  # doit matcher embed_and_store.py
MISTRAL_MODEL = "ministral-8b-latest"  # gratuit / peu cher, largement suffisant ici
TOP_K = 5

SYSTEM_PROMPT = """Tu es un assistant RH pour Clark County. Tu réponds aux questions \
des employés UNIQUEMENT à partir du contexte fourni ci-dessous, extrait du \
HR Policy Manual.

Règles strictes :
- Si la réponse ne se trouve pas dans le contexte, dis clairement que tu ne \
sais pas / que ce n'est pas couvert par le manuel. Ne devine jamais.
- Cite le(s) numéro(s) de section (section_id) sur lesquels tu t'appuies.
- Sois concis et factuel.
"""


def embed_query(co_client: cohere.Client, query: str) -> list[float]:
    """
    Embedding de la question. input_type="search_query" (différent de
    "search_document" utilisé côté ingestion) car Cohere optimise
    différemment selon le rôle du texte.
    """
    response = co_client.embed(
        texts=[query],
        model=COHERE_MODEL,
        input_type="search_query",
    )
    return response.embeddings[0]


def retrieve(qdrant: QdrantClient, query_vector: list[float], top_k: int = TOP_K) -> list[dict]:
    """
    Recherche dense simple dans Qdrant. Retourne les payloads des chunks
    les plus proches, avec leur score de similarité.
    """
    results = qdrant.search(
        collection_name=QDRANT_COLLECTION_NAME,
        query_vector=query_vector,
        limit=top_k,
    )

    return [
        {
            "score": hit.score,
            "chunk_id": hit.payload["chunk_id"],
            "section_id": hit.payload["section_id"],
            "title": hit.payload["title"],
            "text": hit.payload["text"],
        }
        for hit in results
    ]


def build_context(chunks: list[dict]) -> str:
    """
    Assemble les chunks récupérés en un bloc de contexte lisible,
    avec leur section_id pour permettre la citation.
    """
    blocks = []
    for c in chunks:
        blocks.append(
            f"[Section {c['section_id']} - {c['title']}]\n{c['text']}"
        )
    return "\n\n---\n\n".join(blocks)


def generate_answer(llm: ChatMistralAI, query: str, context: str) -> str:
    """
    Appelle Mistral (via LangChain) avec le contexte récupéré + la question
    de l'employé. On passe un SystemMessage (les règles) et un HumanMessage
    (contexte + question), comme le ferait n'importe quelle chaîne LangChain.
    """
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Contexte :\n\n{context}\n\nQuestion : {query}"),
    ]
    response = llm.invoke(messages)
    return response.content


def run_rag(query: str, top_k: int = TOP_K, verbose: bool = True) -> dict:
    """
    Exécute le pipeline complet et retourne un dict avec la question,
    les chunks récupérés et la réponse générée (utile plus tard pour
    RAGAS : il faut garder trace des "contexts" utilisés).
    """
    cohere_api_key = os.getenv("COHERE_API_KEY")
    mistral_api_key = os.getenv("MISTRAL_API_KEY")

    if not cohere_api_key:
        raise ValueError("COHERE_API_KEY introuvable dans .env")
    if not mistral_api_key:
        raise ValueError("MISTRAL_API_KEY introuvable dans .env")

    co = cohere.Client(cohere_api_key)
    llm = ChatMistralAI(
        model=MISTRAL_MODEL,
        mistral_api_key=mistral_api_key,
        temperature=0.1,  # on veut du factuel, pas de créativité
    )
    qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    query_vector = embed_query(co, query)
    chunks = retrieve(qdrant, query_vector, top_k=top_k)
    context = build_context(chunks)
    answer = generate_answer(llm, query, context)

    result = {
        "query": query,
        "retrieved_chunks": chunks,
        "context": context,
        "answer": answer,
    }

    if verbose:
        print("=" * 70)
        print(f"QUESTION : {query}")
        print("=" * 70)

        print(f"\n--- Chunks récupérés (top {top_k}) ---")
        for c in chunks:
            preview = c["text"][:100].replace("\n", " ")
            print(f"  [{c['section_id']}] {c['title']} (score={c['score']:.3f})")
            print(f"      {preview}...")

        print("\n--- Réponse générée ---")
        print(answer)
        print()

    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python -m rag.simple_rag "ta question ici"')
        sys.exit(1)

    user_query = " ".join(sys.argv[1:])
    run_rag(user_query)