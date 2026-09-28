"""
app/api/routes/chat.py

Route de chat : relie authentification, agent (RAG + MCP tools) et
mémoire conversationnelle. C'est le point d'entrée que le frontend
appellera pour parler à l'assistant RH.
"""

from uuid import uuid4

from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from app.api.deps import get_current_context, RequestContext
from app.agent.graph import build_agent

router = APIRouter(prefix="/chat", tags=["chat"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None  # si absent, une nouvelle conversation est créée


class ChatResponse(BaseModel):
    conversation_id: str
    reply: str


@router.post("", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    request: Request,
    access_token: str = Depends(oauth2_scheme),
    context: RequestContext = Depends(get_current_context),
) -> ChatResponse:
    """
    Envoie un message à l'agent HR et retourne sa réponse.

    - access_token : le JWT brut, retransmis tel quel au serveur MCP
      pour que son middleware puisse l'authentifier.
    - context : l'identité déjà décodée, utilisée ici pour construire
      un thread_id qui isole les conversations par employé.
    """
    conversation_id = body.conversation_id or str(uuid4())

    # Le thread_id inclut employee_id pour garantir qu'un utilisateur ne
    # peut jamais, même par erreur côté client, retomber sur le thread
    # d'un autre employé en devinant un conversation_id.
    thread_id = f"{context.employee_id}:{conversation_id}"

    retriever = request.app.state.retriever
    checkpointer = request.app.state.checkpointer

    agent = await build_agent(
        access_token=access_token,
        retriever=retriever,
        checkpointer=checkpointer,
        employee_id=context.employee_id,
    )

    result = await agent.ainvoke(
        {"messages": [("user", body.message)]},
        config={"configurable": {"thread_id": thread_id}},
    )

    last_message = result["messages"][-1]

    return ChatResponse(
        conversation_id=conversation_id,
        reply=last_message.content,
    )