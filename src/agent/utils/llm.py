import os
from langchain_google_genai import ChatGoogleGenerativeAI

from typing import Literal
from dotenv import load_dotenv

load_dotenv()

def get_llm(mode: Literal["fast", "fastest", "smart"]) -> ChatGoogleGenerativeAI:
    """Returns the configured ChatGoogleGenerativeAI instance."""
    # Ensure GOOGLE_API_KEY is set in the environment or .env
    if mode == "fast":
        return ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
        )
    elif mode == "fastest":
        return ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
        )
    elif mode == "smart":
        return ChatGoogleGenerativeAI(
            model="gemini-2.5-pro",
        )
    else:
        raise ValueError("Invalid mode. Must be either 'fast' or 'slow'")
