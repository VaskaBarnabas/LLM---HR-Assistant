import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv(Path(__file__).parent.parent.parent / "backend" / ".env")

SYSTEM_PROMPT = (
    "You are a Linguistic Neutralization Agent. Your task is to identify job titles, roles, "
    "or nouns that contain gendered suffixes or roots (e.g., 'üzletasszony', 'titkárnő', "
    "'pincérlány'). Replace these with their gender-neutral professional equivalents "
    "(e.g., 'üzleti szakember', 'titkár', 'felszolgáló'). You must ensure that the replaced "
    "word fits the original sentence structure and maintains the professional context. "
    "Output only the modified text."
)

_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0,
)


def anonymize(text: str) -> str:
    """Replace gendered job titles and nouns with gender-neutral equivalents."""
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=text),
    ]
    response = _llm.invoke(messages)
    return response.content
