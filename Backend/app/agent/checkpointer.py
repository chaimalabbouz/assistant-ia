"""
app/agent/checkpointer.py

Mémoire conversationnelle de l'agent, persistée dans un fichier SQLite
local via langgraph-checkpoint-sqlite. Choix fait pour compatibilité
avec l'environnement Python 32-bit (psycopg/postgres n'a pas de wheel
32-bit disponible). Pour un volume de démo/projet, SQLite est largement
suffisant et évite cette dépendance native.

Chaque conversation est identifiée par un thread_id (voir chat.py) et
son historique est automatiquement sauvegardé/relu par LangGraph entre
les appels.
"""

import aiosqlite
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from pathlib import Path

CHECKPOINT_DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "checkpoints.sqlite"


async def init_checkpointer() -> AsyncSqliteSaver:
    """
    Crée et prépare le checkpointer SQLite (crée les tables internes
    de LangGraph si elles n'existent pas encore).

    À appeler une fois dans le lifespan de app/main.py, et à garder
    dans app.state pour réutilisation à chaque requête de chat.
    """
    CHECKPOINT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = await aiosqlite.connect(str(CHECKPOINT_DB_PATH))
    checkpointer = AsyncSqliteSaver(conn)
    await checkpointer.setup()
    return checkpointer