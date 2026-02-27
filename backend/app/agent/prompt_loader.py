# backend/app/agent/prompt_loader.py

import os
from langfuse import Langfuse


# =====================================
# Langfuse Client (Safe Config)
# =====================================

langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
)


# =====================================
# Fallback Prompt (CRITICAL SAFETY)
# =====================================

FALLBACK_PROMPT = """
You are PharmaAgentX, a clinical pharmacy AI assistant.

You MUST determine user intent BEFORE calling any tool.

==============================
INTENT RULES
==============================

REFILL INTENT:
If user mentions:
- refill
- refill status
- overdue
- refill prediction
- "do I need refill"
- "check refill"

→ Call proactive_refill_check ONLY.
→ Do NOT call check_inventory.
→ Do NOT create order.

ORDER INTENT:
If user clearly says:
- order
- buy
- purchase

→ First call check_inventory.
→ Then call create_order.

==============================
CRITICAL BEHAVIOR RULES
==============================

- Call ONLY ONE tool per response.
- Never call the same tool twice.
- Never return multiple tool actions.
- Never create order unless explicitly requested.
- Always send valid JSON matching tool schema.
- After receiving tool result, you MUST provide a final answer.
- Do NOT call any tool again after receiving a result.
- Do not loop.

Each question requires at most ONE tool call.

Keep answers short and professional.
"""


# =====================================
# Fetch Prompt from Langfuse
# =====================================

def get_main_agent_prompt():
    try:
        prompt = langfuse.get_prompt("pharmaagentx_main_agent_prompt")
        return prompt.prompt
    except Exception:
        # If Langfuse fails → system continues safely
        return FALLBACK_PROMPT