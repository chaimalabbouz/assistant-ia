"""
app/agent/rag_tool.py

Expose le retriever hybride comme un tool LangChain, utilisable par
l'agent. Pas de notion d'identité ici : la policy RH est la même
pour tout le monde, pas besoin de scoping.
"""

from langchain_core.tools import tool

from app.rag.hybrid_retriever import HybridRetriever


def make_search_hr_policy_tool(retriever: HybridRetriever):
    """
    Factory : crée le tool en fermeture sur l'instance de retriever déjà
    initialisée au démarrage de l'app (singleton, voir app/main.py).

    On passe le retriever explicitement plutôt que de le recréer ici,
    pour ne jamais recharger BM25/Cohere/Qdrant à chaque appel de tool.
    """

    @tool
    def search_hr_policy(query: str) -> str:
        """
        Search the company HR policy document for information relevant
        to the given query. Use this tool for any question about HR
        rules, benefits, leave policy, or company procedures.

        Returns the most relevant policy excerpts, each with its
        section title and ID. Always cite the section when using
        this information in your answer. If the returned excerpts
        don't actually answer the question, say so explicitly instead
        of guessing.
        """
        results = retriever.search(query, top_k=5)

        if not results:
            return "No relevant policy sections found for this query."

        formatted = []
        for r in results:
            formatted.append(
                f"[Section {r['section_id']} — {r['title']}]\n{r['text']}"
            )
        return "\n\n---\n\n".join(formatted)

    return search_hr_policy