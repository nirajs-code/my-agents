import os
from openai import OpenAI

def create_client(model: str = None) -> OpenAI:
    model = model or os.getenv("MODEL", "")
    if "gemini" in model:
        return OpenAI(api_key=os.getenv("GOOGLE_API_KEY"), base_url=os.getenv("GEMINI_BASE_URL"))
    elif "llama" in model:
        return OpenAI(api_key=os.getenv("OLLAMA_API_KEY"), base_url=os.getenv("OLLAMA_BASE_URL"))
    return OpenAI()
