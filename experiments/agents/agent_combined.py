import os
import time
from pathlib import Path
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai.chat_models import ChatGoogleGenerativeAIError

load_dotenv(Path(__file__).parent.parent.parent / "backend" / ".env")

SYSTEM_PROMPT = """You are a comprehensive CV Anonymization Agent. Process the given CV text and apply ALL of the following anonymization steps:

1. **Names and Personal Identifiers**: Replace all personal names (first names, middle names, surnames) and personal honorifics (Mr., Ms., Mrs., Dr., [Name]né) with '[CANDIDATE]'. Preserve grammatical inflections (e.g., '[CANDIDATE]-nak', '[CANDIDATE]\\'s').

2. **Gendered Job Titles**: Replace job titles, roles, or nouns with gendered suffixes or roots (e.g., 'üzletasszony', 'titkárnő', 'pincérlány') with gender-neutral equivalents (e.g., 'üzleti szakember', 'titkár', 'felszolgáló'). Preserve sentence structure and professional context.

3. **Pronouns and References**: Replace gender-specific pronouns (he, she, his, her, hers, him) with gender-neutral alternatives (they, their, them, the candidate). Apply to any English-language sections or citations within the CV.

4. **Family and Marital Status**: Replace or neutralize information about marital status, parenthood, or family roles (husband, wife, mother, father, maiden name, married) with '[PERSONAL DATA]' or rephrase to remove gendered familial context while keeping the professional timeline intact.

5. **Gender-Linked Life Events**: Neutralize life events that indirectly reveal gender (maternity leave, paternity leave, military service, women's choir, boy's scout) using broader professional terms (career break, public service, community organization). Preserve timeframes and activities.

Output ONLY the fully anonymized text. No explanation, no commentary, no markdown formatting."""

_llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-lite",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0,
)

_RETRY_DELAYS = [20, 40, 60]  # seconds between retries on rate-limit


def anonymize(text: str) -> str:
    """Apply all 5 anonymization tasks in a single LLM call.

    Retries automatically on 429 rate-limit errors with increasing delays.
    """
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=text),
    ]
    last_err = None
    for attempt, delay in enumerate([0] + _RETRY_DELAYS):
        if delay:
            print(f"[Agent] Rate limit hit, retrying in {delay}s (attempt {attempt + 1}/{len(_RETRY_DELAYS) + 1})...")
            time.sleep(delay)
        try:
            return _llm.invoke(messages).content
        except ChatGoogleGenerativeAIError as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                last_err = e
                continue
            raise
    raise last_err
