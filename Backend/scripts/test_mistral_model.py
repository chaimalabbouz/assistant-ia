"""
scripts/test_mistral_models.py

Teste plusieurs modèles Mistral l'un après l'autre, avec une pause
entre chaque pour éviter le rate limiting du tier gratuit.

Usage: python -m scripts.test_mistral_models
"""

import asyncio
from dotenv import load_dotenv

load_dotenv()

from langchain_mistralai import ChatMistralAI

MODELS_TO_TEST = [
    "mistral-small-latest",
    "ministral-8b-latest",
    "mistral-medium-latest",
    "open-mistral-nemo",
]

DELAY_BETWEEN_CALLS_SECONDS = 5


async def test_model(model_name: str) -> None:
    llm = ChatMistralAI(model=model_name, temperature=0.1)
    try:
        response = await llm.ainvoke("Say 'hello' in one word.")
        print(f"✅ {model_name} — OK — réponse: {response.content!r}")
    except Exception as e:
        print(f"❌ {model_name} — {e}")


async def main():
    for model_name in MODELS_TO_TEST:
        await test_model(model_name)
        await asyncio.sleep(DELAY_BETWEEN_CALLS_SECONDS)


if __name__ == "__main__":
    asyncio.run(main())