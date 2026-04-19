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
        "You are a Pronoun and Reference Neutralization Agent. Scan the text for any "
        "gender-specific pronouns (he, she, his, her, hers, him) or gendered references. "
        "Replace them with gender-neutral alternatives such as 'they', 'their', 'them', or "
        "'the candidate'. Pay special attention to citations or English-language sections within "
        "the CV. In Hungarian context, look for phrases that function as gendered references. "
        "Output only the modified text."
    ),
    "family_status": (
        "You are a Family Status Anonymization Agent. Identify and remove or neutralize any "
        "information regarding marital status, parenthood, or family roles. This includes terms "
        "like 'husband', 'wife', 'mother', 'father', 'maiden name', or 'married'. Replace these "
        "phrases with '[PERSONAL DATA]' or rephrase the sentence to remove the gendered familial "
        "context without losing the underlying professional timeline. Output only the modified text."
    ),
    "life_events": (
        "You are a Contextual Bias Removal Agent. Your task is to identify life events or social "
        "experiences that indirectly reveal gender (e.g., 'maternity leave', 'paternity leave', "
        "'military service', 'women\\'s choir', 'boy\\'s scout'). Neutralize these by using broader "
        "professional terms such as 'career break', 'public service', or 'community organization'. "
        "The goal is to preserve the timeframe and activity while removing the gendered nature of "
        "the event. Output only the modified text."
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
# Anonymization LangGraph pipeline
# ---------------------------------------------------------------------------

class AnonState(TypedDict):
    current_text: str


def node_names(state: AnonState) -> AnonState:
    print("[Agent 1/5] Anonymizing names and honorifics...")
    return {"current_text": _run_agent(_llm_names, _PROMPTS["names"], state["current_text"])}


def node_gendered_nouns(state: AnonState) -> AnonState:
    print("[Agent 2/5] Neutralizing gendered job titles and nouns...")
    return {"current_text": _run_agent(_llm_gendered_nouns, _PROMPTS["gendered_nouns"], state["current_text"])}


def node_pronouns(state: AnonState) -> AnonState:
    print("[Agent 3/5] Replacing gendered pronouns and references...")
    return {"current_text": _run_agent(_llm_pronouns, _PROMPTS["pronouns"], state["current_text"])}


def node_family_status(state: AnonState) -> AnonState:
    print("[Agent 4/5] Removing family and marital status information...")
    return {"current_text": _run_agent(_llm_family_status, _PROMPTS["family_status"], state["current_text"])}


def node_life_events(state: AnonState) -> AnonState:
    print("[Agent 5/5] Neutralizing gender-linked life events...")
    return {"current_text": _run_agent(_llm_life_events, _PROMPTS["life_events"], state["current_text"])}


_anon_graph = StateGraph(AnonState)
_anon_graph.add_node("names", node_names)
_anon_graph.add_node("gendered_nouns", node_gendered_nouns)
_anon_graph.add_node("pronouns", node_pronouns)
_anon_graph.add_node("family_status", node_family_status)
_anon_graph.add_node("life_events", node_life_events)

_anon_graph.add_edge(START, "names")
_anon_graph.add_edge("names", "gendered_nouns")
_anon_graph.add_edge("gendered_nouns", "pronouns")
_anon_graph.add_edge("pronouns", "family_status")
_anon_graph.add_edge("family_status", "life_events")
_anon_graph.add_edge("life_events", END)

anonymization_pipeline = _anon_graph.compile()


def anonymize_text(input_pdf: str) -> str:
    """Run the 5-agent anonymization pipeline, return the anonymized plain text."""
    cv_text = extract_pdf_text(input_pdf)
    final_state = anonymization_pipeline.invoke({"current_text": cv_text})
    return final_state["current_text"]


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
    anonymized_texts: list[str]
    texts: list[str]
    candidates: list[dict]


def anonymize_pdfs_node(state: State) -> State:
    anonymized_texts = []
    for path in state["paths"]:
        print(f"[Anonymize] Processing {Path(path).name}...")
        anonymized_texts.append(anonymize_text(path))
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
