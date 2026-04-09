import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv(Path(__file__).parent.parent.parent / "backend" / ".env")

SYSTEM_PROMPT = (
    "You are a Family Status Anonymization Agent. Identify and remove or neutralize any "
    "information regarding marital status, parenthood, or family roles. This includes terms "
    "like 'husband', 'wife', 'mother', 'father', 'maiden name', or 'married'. Replace these "
    "phrases with '[PERSONAL DATA]' or rephrase the sentence to remove the gendered familial "
    "context without losing the underlying professional timeline. Output only the modified text."
)

_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0,
)


def anonymize(text: str) -> str:
    """Remove or neutralize family and marital status information."""
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=text),
    ]
    response = _llm.invoke(messages)
    return response.content
