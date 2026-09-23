"""
Test isolé Mistral - Ministral 3 8B (ministral-8b-latest)
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("MISTRAL_API_KEY")

response = requests.post(
    "https://api.mistral.ai/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    },
    json={
        "model": "ministral-8b-latest",
        "messages": [{"role": "user", "content": "dis juste OK"}],
    },
)

print("Status code :", response.status_code)
print("Réponse :", response.text[:500])