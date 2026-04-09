import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv(Path(__file__).parent.parent.parent / "backend" / ".env")

SYSTEM_PROMPT = (
    "You are a specialized Data Privacy Agent. Your sole task is to identify and replace "
    "all personal names (first names, middle names, and gendered surnames) and personal "
    "honorifics (e.g., Mr., Ms., Mrs., Dr. [Name]né) in the text. Replace them with the "
    "placeholder '[CANDIDATE]'. If a name appears in a possessive or inflected form, ensure "
    "the placeholder maintains the grammatical role (e.g., '[CANDIDATE]\\'s' or "
    "'[CANDIDATE]-nak'). Do not alter any other professional information. Output only the "
    "modified text."
)

_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0,
)


def anonymize(text: str) -> str:
    """Replace all personal names and honorifics with [CANDIDATE]."""
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=text),
    ]
    response = _llm.invoke(messages)
    return response.content
