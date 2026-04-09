import os

from dotenv import load_dotenv


def load_api_key() -> str:
    load_dotenv()
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError(
            "GEMINI_API_KEY not set. Add it to .env or export it as an environment variable."
        )
    return key
