# backend/app/agent/agent.py

import os
from langchain.agents import initialize_agent, AgentType
from langchain.agents import AgentExecutor

from backend.app.agent.llm_factory import get_llm
from backend.app.agent.tools import (
    check_inventory_tool,
    create_order_tool,
    proactive_refill_tool
)

# ✅ Langfuse v3
from langfuse import Langfuse
from langfuse.langchain import CallbackHandler

# ✅ NEW: Prompt Loader
from backend.app.agent.prompt_loader import get_main_agent_prompt


# =====================================
# Load LLM
# =====================================

llm = get_llm()

# =====================================
# Langfuse Setup (SAFE)
# =====================================

langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
)

langfuse_handler = CallbackHandler()

# =====================================
# Register Tools
# =====================================

tools = [
    check_inventory_tool,
    create_order_tool,
    proactive_refill_tool
]

# =====================================
# LOAD PROMPT FROM LANGFUSE
# =====================================

SYSTEM_PREFIX = get_main_agent_prompt()

# =====================================
# Create Structured Agent
# =====================================

base_agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    agent_kwargs={
        "prefix": SYSTEM_PREFIX
    }
)

# =====================================
# Stability Executor + Langfuse
# =====================================

agent = AgentExecutor.from_agent_and_tools(
    agent=base_agent.agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
    max_iterations=3,
    early_stopping_method="generate",
    callbacks=[langfuse_handler]
)

# =====================================
# Public invoke function
# =====================================

def run_agent(user_input: str):
    response = agent.invoke({
        "input": user_input
    })

    return response["output"]