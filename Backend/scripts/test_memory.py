import os
import sys
import httpx

BASE = "http://127.0.0.1:8000"
EMAIL = os.getenv("TEST_EMAIL")
PASSWORD = "Test1234!"

if not EMAIL:
    sys.exit("Définis d'abord TEST_EMAIL (voir la commande avant le script).")


def login():
    r = httpx.post(
        f"{BASE}/auth/login",
        data={"username": EMAIL, "password": PASSWORD},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def chat(token, message, conv_id=None):
    body = {"message": message}
    if conv_id:
        body["conversation_id"] = conv_id
    r = httpx.post(
        f"{BASE}/chat",
        json=body,
        headers={"Authorization": f"Bearer {token}"},
        timeout=120,
    )
    r.raise_for_status()
    return r.json()


token = login()

if len(sys.argv) > 1:
    # Étape 2 : on réutilise la conversation après redémarrage
    conv_id = sys.argv[1]
    res = chat(token, "Quel mot de test t'ai-je demandé de retenir ?", conv_id)
    print("Réponse :", res["reply"])
else:
    # Étape 1 : première conversation
    res = chat(token, "Retiens ce mot de test : ANANAS. Réponds juste OK.")
    conv_id = res["conversation_id"]
    print("conversation_id :", conv_id)
    print("Réponse 1 :", res["reply"])
    res = chat(token, "Quel mot de test t'ai-je demandé de retenir ?", conv_id)
    print("Réponse 2 :", res["reply"])