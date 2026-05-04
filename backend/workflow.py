from pathlib import Path
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv
import pymupdf
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.messages import SystemMessage, HumanMessage

from backend.chromaClient import add_documents
from backend.utils.path_analizer import analyze_pdf_paths

load_dotenv(Path(__file__).parent / ".env")

# ---------------------------------------------------------------------------
# CV Analysis LLM (local Docker / gemma4)
# ---------------------------------------------------------------------------

llm = ChatOpenAI(
    model="docker.io/ai/gemma4:E4B",
    base_url="http://localhost:12434/v1",
    api_key="docker",
    temperature=0,
)

_parser = JsonOutputParser()

_prompt = PromptTemplate.from_template(
    """You are a Senior HR Specialist. Analyze the CV below and extract information about the candidate.

Return a JSON object with EXACTLY these keys:
- "name": full name as a string
- "email": email address as a string
- "phone": phone number as a string
- "location": city/address as a string
- "skills": flat array of skill strings (technologies, competencies, soft skills)
- "languages": array of language strings (e.g. "English (Fluent)")

Return ONLY the JSON object, no other text.

CV:
{cv_text}

{format_instructions}""",
    partial_variables={"format_instructions": _parser.get_format_instructions()},
)

text_extraction_chain = _prompt | llm | _parser


# ---------------------------------------------------------------------------
# Anonymization LLMs (reuse local Docker llm)
# ---------------------------------------------------------------------------

def _make_anon_llm() -> ChatOpenAI:
    return llm


_PROMPTS = {
    "names": (
        "You are a specialized Data Privacy Agent. Your sole task is to identify and replace "
        "all personal names (first names, middle names, and gendered surnames) and personal "
        "honorifics (e.g., Mr., Ms., Mrs., Dr. [Name]né) in the text. Replace them with the "
        "placeholder '[CANDIDATE]'. If a name appears in a possessive or inflected form, ensure "
        "the placeholder maintains the grammatical role (e.g., '[CANDIDATE]\\'s' or "
        "'[CANDIDATE]-nak'). Do not alter any other professional information. Output only the "
        "modified text."
    ),
    "gendered_nouns": (
        "You are a Linguistic Neutralization Agent. Your task is to identify job titles, roles, "
        "or nouns that contain gendered suffixes or roots in ANY language — including English and Hungarian. "
        "English examples: 'fireman' → 'firefighter', 'fisherman/fishermen' → 'fisher/fishers', "
        "'crewman/crewmen' → 'crew member/crew members', 'spokesman/spokesmen' → 'spokesperson/spokespersons', "
        "'chairman' → 'chairperson', 'stewardess' → 'flight attendant', 'actress' → 'actor', "
        "'waitress' → 'server', 'steward/stewardess' → 'flight attendant', 'salesman' → 'salesperson', "
        "'policeman' → 'police officer', 'businessman' → 'business professional'. "
        "Hungarian examples: 'üzletasszony' → 'üzleti szakember', 'titkárnő' → 'titkár', "
        "'pincérlány' → 'felszolgáló'. "
        "Replace each gendered term with its gender-neutral professional equivalent. "
        "Preserve plurals, inflections, and sentence structure. "
        "Output only the modified text."
    ),
    "pronouns": (
        "You are a Pronoun Neutralization Agent. Your sole task is to replace gender-specific "
        "pronouns with gender-neutral equivalents. Specifically: replace 'he', 'him', 'his', "
        "'himself', 'she', 'her', 'hers', 'herself' with 'they', 'them', 'their', 'themselves', "
        "or 'the candidate' where grammatically appropriate. "
        "IMPORTANT: Do NOT change job titles, role names, or any nouns — only pronouns. "
        "Do NOT change words like 'stewardess', 'fireman', 'chairman', 'mother', 'husband', etc. "
        "In Hungarian context, replace gendered personal pronouns with gender-neutral equivalents. "
        "Output only the modified text."
    ),
    "family_status": (
        "You are a Family Status Anonymization Agent. Identify and remove or neutralize explicit "
        "references to marital status and family roles. This includes terms like 'husband', 'wife', "
        "'married', 'single', 'divorced', 'maiden name', 'children', 'son', 'daughter', 'father', "
        "'mother', 'parent'. Replace these with '[PERSONAL DATA]' or rephrase to preserve the "
        "professional timeline without the personal detail. "
        "IMPORTANT: Do NOT replace gender pronouns (he, she, his, her, they, etc.). "
        "Do NOT touch life-event terms like 'maternity leave', 'paternity leave', or 'career break' "
        "— those are handled by a separate agent. "
        "Output only the modified text."
    ),
    "life_events": (
        "You are a Contextual Bias Removal Agent. Your task is to neutralize specific life events "
        "that directly reveal gender. ONLY neutralize explicit gendered events such as: "
        "'maternity leave', 'paternity leave', 'military service', 'women\\'s choir', 'boy\\'s scout', "
        "'conscription', and similar explicitly gendered personal life events. "
        "Replace them with neutral equivalents: 'career break', 'public service', 'community organization', etc., "
        "preserving the timeframe and professional context. "
        "IMPORTANT: Do NOT change job titles or professional role names (e.g., stewardess, fireman, actress). "
        "Do NOT change pronouns. Only target the specific life-event terms listed above. "
        "Output only the modified text."
    ),
}

_llm_names = _make_anon_llm()
_llm_gendered_nouns = _make_anon_llm()
_llm_pronouns = _make_anon_llm()
_llm_family_status = _make_anon_llm()
_llm_life_events = _make_anon_llm()


def _run_agent(llm: ChatOpenAI, prompt: str, text: str) -> str:
    response = llm.invoke([SystemMessage(content=prompt), HumanMessage(content=text)])
    return response.content


# ---------------------------------------------------------------------------
# PDF helpers
# ---------------------------------------------------------------------------

def extract_pdf_text(pdf_path: str) -> str:
    doc = pymupdf.open(pdf_path)
    text = "".join(page.get_text() for page in doc)
    doc.close()
    return text


# ---------------------------------------------------------------------------
# Anonymization pipeline (sequential, filter-aware)
# ---------------------------------------------------------------------------

_AGENT_ORDER: list[tuple[str, ChatOpenAI]] = [
    ("names", _llm_names),
    ("gendered_nouns", _llm_gendered_nouns),
    ("pronouns", _llm_pronouns),
    ("family_status", _llm_family_status),
    ("life_events", _llm_life_events),
]


def anonymize_text(input_pdf: str, filters: dict | None = None) -> str:
    """Run the anonymization agents sequentially, skipping any disabled by filters.

    filters: dict with keys matching _PROMPTS; True = run, False = skip.
    If filters is None or a key is missing, the agent runs by default.
    """
    if filters is None:
        filters = {}

    text = extract_pdf_text(input_pdf)
    for i, (key, agent_llm) in enumerate(_AGENT_ORDER, 1):
        if filters.get(key, True):
            print(f"[Agent {i}/5] Running '{key}'...")
            text = _run_agent(agent_llm, _PROMPTS[key], text)
        else:
            print(f"[Agent {i}/5] Skipping '{key}' (disabled by job config)")
    return text


def _esc(text: str) -> str:
    """HTML-escape a plain-text string to prevent XSS."""
    return (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def anonymized_text_to_html(text: str) -> str:
    """Convert plain anonymized CV text to structured, XSS-safe HTML for display."""
    lines = text.split("\n")
    html_parts: list[str] = []
    in_list = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            continue

        is_bullet = stripped.startswith(("•", "-", "*")) and len(stripped) > 1

        if is_bullet:
            if not in_list:
                html_parts.append('<ul class="cv-list">')
                in_list = True
            html_parts.append(f"<li>{_esc(stripped[1:].strip())}</li>")
        else:
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            is_header = (
                (stripped.isupper() and len(stripped) < 60)
                or (len(stripped) < 50 and stripped[0].isupper() and stripped.endswith(":"))
            )
            if is_header:
                html_parts.append(f'<h3 class="cv-section">{_esc(stripped.rstrip(":"))}</h3>')
            else:
                html_parts.append(f"<p>{_esc(stripped)}</p>")

    if in_list:
        html_parts.append("</ul>")

    return "\n".join(html_parts)


# ---------------------------------------------------------------------------
# Main workflow
# ---------------------------------------------------------------------------

class State(TypedDict):
    paths: list[str]
    filters: dict
    anonymized_texts: list[str]
    texts: list[str]
    candidates: list[dict]


def anonymize_pdfs_node(state: State) -> State:
    filters = state.get("filters") or {}
    anonymized_texts = []
    for path in state["paths"]:
        print(f"[Anonymize] Processing {Path(path).name}...")
        anonymized_texts.append(anonymize_text(path, filters))
    return {"anonymized_texts": anonymized_texts}


def pdf_to_text_node(state: State) -> State:
    cv_texts = analyze_pdf_paths(state["paths"])
    return {"texts": cv_texts}


def text_to_vectordb_node(state: State) -> State:
    add_documents(state["texts"])
    return state


def analyze_cv_node(state: State) -> State:
    candidates = [text_extraction_chain.invoke({"cv_text": text}) for text in state["texts"]]
    return {"candidates": candidates}


def print_candidates_node(state: State) -> State:
    for i, candidate in enumerate(state["candidates"], start=1):
        print(f"Candidate {i}")
        print("-" * 40)
        for key, value in candidate.items():
            if isinstance(value, list):
                print(f"{key.capitalize()}:")
                for item in value:
                    print(f"  - {item}")
            else:
                print(f"{key.capitalize()}: {value}")
        print("\n")
    return state


workflow = StateGraph(State)

workflow.add_node("anonymize_pdfs", anonymize_pdfs_node)
workflow.add_node("pdf_to_text", pdf_to_text_node)
workflow.add_node("text_to_vectordb", text_to_vectordb_node)
workflow.add_node("analyze_cv", analyze_cv_node)
workflow.add_node("print_candidates", print_candidates_node)

workflow.add_edge(START, "anonymize_pdfs")
workflow.add_edge("anonymize_pdfs", "pdf_to_text")
workflow.add_edge("pdf_to_text", "text_to_vectordb")
workflow.add_edge("text_to_vectordb", "analyze_cv")
workflow.add_edge("analyze_cv", "print_candidates")
workflow.add_edge("print_candidates", END)

chain = workflow.compile()
