"""
app/agent/llm.py

Configuration du modèle Mistral utilisé par l'agent, via LangChain.
La clé API est lue automatiquement depuis MISTRAL_API_KEY (.env).
"""

from langchain_mistralai import ChatMistralAI

def get_llm() -> ChatMistralAI:
    """
    Retourne une instance du modèle Mistral configurée pour l'agent.

    temperature basse : on veut des réponses factuelles et cohérentes
    (données RH, policy) plutôt que créatives.
    """
    return ChatMistralAI(
        model="open-mistral-nemo",
        temperature=0.1,
    )