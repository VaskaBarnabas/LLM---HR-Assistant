import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv(Path(__file__).parent.parent.parent / "backend" / ".env")

SYSTEM_PROMPT = (
    "You are a Pronoun and Reference Neutralization Agent. Scan the text for any "
    "gender-specific pronouns (he, she, his, her, hers, him) or gendered references. "
    "Replace them with gender-neutral alternatives such as 'they', 'their', 'them', or "
    "'the candidate'. Pay special attention to citations or English-language sections within "
    "the CV. In Hungarian context, look for phrases that function as gendered references. "
    "Output only the modified text."
)

_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0,
)


def anonymize(text: str) -> str:
    """Replace gendered pronouns and references with neutral alternatives."""
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=text),
    ]
    response = _llm.invoke(messages)
    return response.content
