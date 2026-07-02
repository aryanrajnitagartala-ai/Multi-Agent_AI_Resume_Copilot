"""
Configuration constants for the Job Search LLM App.
"""

import os
from openai import OpenAI

GROQ_BASE_URL = "https://api.groq.com/openai/v1"

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
LLM_MODEL = "llama-3.3-70b-versatile"


def get_llm_client() -> OpenAI:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Add it to your .env file locally, "
            "or to your Modal secret when deploying. Get a free key at "
            "https://console.groq.com/keys"
        )
    return OpenAI(
        api_key=api_key,
        base_url=GROQ_BASE_URL,
    )


VECTOR_DB_DIR = "job_vectorstore"
COLLECTION_NAME = "jobs"

TOP_K_MATCHES = 5
MATCH_SCORE_THRESHOLD = 0.8

PUSHOVER_URL = "https://api.pushover.net/1/messages.json"
NOTIFICATION_SOUND = "magic"
