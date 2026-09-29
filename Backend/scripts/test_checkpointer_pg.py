import asyncio
import os
import sys

# psycopg async ne marche pas avec la boucle par défaut de Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

os.environ["CHECKPOINTER_BACKEND"] = "postgres"

import psycopg

from app.agent.checkpointer import init_checkpointer, close_checkpointer
from app.config import CHECKPOINT_DB_URI


async def main():
    cp = await init_checkpointer()

    async with await psycopg.AsyncConnection.connect(
        CHECKPOINT_DB_URI, autocommit=True
    ) as conn:
        cur = await conn.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_name LIKE 'checkpoint%' "
            "ORDER BY 1"
        )
        rows = await cur.fetchall()

    print("Tables trouvées :", [r[0] for r in rows])

    res = await cp.aget_tuple({"configurable": {"thread_id": "thread-inexistant"}})
    print("Lecture d'un thread inexistant (attendu: None) :", res)

    await close_checkpointer()
    print("TEST OK")


asyncio.run(main())