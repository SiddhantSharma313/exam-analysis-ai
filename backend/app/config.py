import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "nousresearch/hermes-3-llama-3.1-405b:free")
    LLM_BASE_URL: str = "https://openrouter.ai/api/v1"
    LLM_TIMEOUT: int = int(os.getenv("LLM_TIMEOUT", "30"))
    MAX_DOC_CHARS: int = 8000
    TOPIC_LIMIT: int = 12


settings = Settings()
