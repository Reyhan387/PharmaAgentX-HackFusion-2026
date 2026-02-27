import os
from dotenv import load_dotenv

load_dotenv()

def get_llm():
    provider = os.getenv("LLM_PROVIDER")

    if provider == "ollama":
        from langchain_community.chat_models import ChatOllama
        return ChatOllama(
            model=os.getenv("OLLAMA_MODEL", "mistral"),
            temperature=0
        )

    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0,
            api_key=os.getenv("OPENAI_API_KEY")
        )

    else:
        raise ValueError("Invalid LLM_PROVIDER in .env")