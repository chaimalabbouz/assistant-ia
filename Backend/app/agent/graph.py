"""
app/agent/graph.py

Assemblage de l'agent principal via LangGraph (pattern ReAct).

Comme les tools MCP dépendent du token de l'utilisateur courant
(voir mcp_client.py), l'agent ne peut PAS être un singleton global
comme le retriever RAG — il doit être reconstruit à chaque requête,
avec les tools (RAG + MCP) propres à cette requête.

Le checkpointer (mémoire), lui, reste partagé/singleton (voir
checkpointer.py) : c'est le stockage qui est global, pas l'agent.
"""

from langgraph.prebuilt import create_react_agent

from app.agent.llm import get_llm
from app.agent.rag_tool import make_search_hr_policy_tool
from app.agent.mcp_client import get_mcp_tools
from app.rag.hybrid_retriever import HybridRetriever
from app.agent.ticket_tool import make_create_hr_ticket_tool

SYSTEM_PROMPT = """You are the HR Assistant for this company. You help employees \
with questions about company HR policy and their own personal HR data \
(profile, manager, leave balance).

Tools available to you:
- search_hr_policy: search the official HR policy document. Use it for any \
question about rules, benefits, leave policy, or procedures.
- get_my_profile, get_my_manager, get_my_leave_balance: return data about \
the employee currently talking to you. These tools take no parameters — \
they always refer to the current user, never anyone else.
- get_department_info: general information about a company department.
- create_hr_ticket: escalate a question to the HR team when it is outside \
your scope.

Rules you must always follow:
1. For policy questions, answer ONLY using information returned by \
search_hr_policy. Never rely on general knowledge about HR practices. \
Always cite the section (e.g. "According to section 11.6 — Sick Leave...").
2. If search_hr_policy returns nothing relevant to the question, say clearly \
that you couldn't find this information in the company policy — do not guess.
3. You can only access the personal data of the employee you are currently \
talking to. You have no way to access another employee's data, and you must \
never claim otherwise.
4. If a question involves a legal dispute, harassment or discrimination \
concern, salary negotiation, a request to change personal data, or any \
topic you cannot answer reliably, use create_hr_ticket instead of attempting \
an answer yourself. Confirm to the employee that their question has been \
forwarded to HR.
5. When summarizing information from the HR policy, report figures and \
durations exactly as stated in the source — never merge or generalize two \
different numbers (e.g. different leave durations for different benefits) \
into a single claim.
6. Be concise and professional. This is a workplace assistant, not a casual \
chatbot.
"""


async def build_agent(access_token: str, retriever: HybridRetriever, checkpointer, employee_id: str):
    """
    Construit l'agent pour une requête donnée : rassemble les tools RAG
    et MCP (ces derniers liés au token de l'utilisateur courant), et
    compile le graphe ReAct avec la mémoire (checkpointer) branchée.

    À appeler à chaque requête de chat — pas un singleton, contrairement
    au retriever ou au checkpointer eux-mêmes.
    """
    rag_tool = make_search_hr_policy_tool(retriever)
    mcp_tools = await get_mcp_tools(access_token)
    ticket_tool = make_create_hr_ticket_tool(employee_id)

    all_tools = [rag_tool, ticket_tool, *mcp_tools]

    agent = create_react_agent(
        model=get_llm(),
        tools=all_tools,
        state_modifier=SYSTEM_PROMPT,
        checkpointer=checkpointer,
    )

    return agent