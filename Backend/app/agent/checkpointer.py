"""
app/agent/checkpointer.py

Mémoire conversationnelle de l'agent.
- CHECKPOINTER_BACKEND=sqlite (défaut) : fichier local, comme avant.
- CHECKPOINTER_BACKEND=postgres : Postgres (Neon), pour Render/Docker.
"""

import os
from pathlib import Path

CHECKPOINT_DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "checkpoints.sqlite"

_resources = []  # connexions à fermer à l'arrêt


async def init_checkpointer():
    backend = os.getenv("CHECKPOINTER_BACKEND", "sqlite").lower()

    if backend == "postgres":
        from psycopg.rows import dict_row
        from psycopg_pool import AsyncConnectionPool
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        from app.config import CHECKPOINT_DB_URI

        pool = AsyncConnectionPool(
            conninfo=CHECKPOINT_DB_URI,
            min_size=1,
            max_size=5,
            max_idle=60,
            max_lifetime=300,
            check=AsyncConnectionPool.check_connection,
            kwargs={
                "autocommit": True,
                "prepare_threshold": None,  # requis avec le pooler Neon
                "row_factory": dict_row,
            },
            open=False,
        )
        await pool.open()
        _resources.append(pool)

        checkpointer = AsyncPostgresSaver(pool)
        await checkpointer.setup()
        print("Checkpointer : Postgres")
        return checkpointer

    import aiosqlite
    from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

    CHECKPOINT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = await aiosqlite.connect(str(CHECKPOINT_DB_PATH))
    _resources.append(conn)

    checkpointer = AsyncSqliteSaver(conn)
    await checkpointer.setup()
    print("Checkpointer : SQLite")
    return checkpointer


async def close_checkpointer():
    for r in _resources:
        await r.close()
    _resources.clear()