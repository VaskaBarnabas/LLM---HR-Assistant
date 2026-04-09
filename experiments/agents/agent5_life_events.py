import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv(Path(__file__).parent.parent.parent / "backend" / ".env")

SYSTEM_PROMPT = (
    "You are a Contextual Bias Removal Agent. Your task is to identify life events or social "
    "experiences that indirectly reveal gender (e.g., 'maternity leave', 'paternity leave', "
    "'military service', 'women\\'s choir', 'boy\\'s scout'). Neutralize these by using broader "
    "professional terms such as 'career break', 'public service', or 'community organization'. "
    "The goal is to preserve the timeframe and activity while removing the gendered nature of "
    "the event. Output only the modified text."
)

_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0,
)


def anonymize(text: str) -> str:
    """Neutralize gender-linked life events and social experiences."""
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=text),
    ]
    response = _llm.invoke(messages)
    return response.content
