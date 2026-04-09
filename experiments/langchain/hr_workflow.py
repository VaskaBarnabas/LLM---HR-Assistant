from difflib import SequenceMatcher
from pathlib import Path
import os

import pymupdf
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict

load_dotenv()

# ---------------------------------------------------------------------------
# CV Analysis (used by backend.py)
# ---------------------------------------------------------------------------

_analysis_model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0,
)

_analysis_template = """You are a Senior HR Specialist. Extract information from the CVs below and return a JSON array.

Each element must have EXACTLY these keys:
- "name": full name as a string
- "email": email address as a string
- "phone": phone number as a string
- "location": city/address as a string
- "skills": flat array of skill strings (combine all technologies, competencies, soft skills)
- "languages": array of language strings (e.g. "English (Fluent)")

Return ONLY the JSON array, no other text.

CVs (separated by blank lines):

{cv_text}

{format_instructions}
"""

_parser = JsonOutputParser()
_analysis_chain = (
    PromptTemplate.from_template(
        _analysis_template,
        partial_variables={"format_instructions": _parser.get_format_instructions()},
    )
    | _analysis_model
    | _parser
)


def analyze_pdf_paths(paths: list[str]) -> list[dict]:
    """Load PDFs from file paths, analyze with LLM, return list of candidate dicts."""
    texts = []
    for path in paths:
        loader = PyPDFLoader(path)
        pages = loader.load()
        texts.append("\n".join(p.page_content for p in pages))
    cv_text = "\n\n".join(texts)
    result = _analysis_chain.invoke({"cv_text": cv_text})
    return result if isinstance(result, list) else result.get("candidates", [result])


# ---------------------------------------------------------------------------
# Anonymization agents (one LLM per agent)
# ---------------------------------------------------------------------------

def _make_llm() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite",
        google_api_key=os.getenv("GEMINI_API_KEY"),
        temperature=0,
    )


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
        "or nouns that contain gendered suffixes or roots (e.g., 'üzletasszony', 'titkárnő', "
        "'pincérlány'). Replace these with their gender-neutral professional equivalents "
        "(e.g., 'üzleti szakember', 'titkár', 'felszolgáló'). You must ensure that the replaced "
        "word fits the original sentence structure and maintains the professional context. "
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

_llm_names = _make_llm()
_llm_gendered_nouns = _make_llm()
_llm_pronouns = _make_llm()
_llm_family_status = _make_llm()
_llm_life_events = _make_llm()


def _run_agent(llm: ChatGoogleGenerativeAI, prompt: str, text: str) -> str:
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


def _span_style_at(page, rect):
    for block in page.get_text("dict")["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                if pymupdf.Rect(span["bbox"]).intersects(rect):
                    flags = span["flags"]
                    is_bold = bool(flags & 16)
                    is_italic = bool(flags & 2)
                    if is_bold and is_italic:
                        fontname = "hebi"
                    elif is_bold:
                        fontname = "hebo"
                    elif is_italic:
                        fontname = "heit"
                    else:
                        fontname = "helv"
                    c = span.get("color", 0)
                    r, g, b = ((c >> 16) & 0xFF) / 255, ((c >> 8) & 0xFF) / 255, (c & 0xFF) / 255
                    # Ha a szín fehér vagy közel fehér, visszaesünk feketére
                    color = (0, 0, 0) if (r > 0.9 and g > 0.9 and b > 0.9) else (r, g, b)
                    return span["size"], fontname, color
    return 11, "helv", (0, 0, 0)


def _build_pdf_from_scratch(anonymized_text: str, input_pdf: str, output_pdf: str) -> None:
    """Build a new PDF from scratch using word-level position matching.

    Rasterizes each original page as background, then covers changed words
    with white rectangles and writes replacement text on top.
    Uses get_text("words") for exact word-boundary matching — prevents
    partial-word hits (e.g. 'he' inside 'the').
    """
    anon_words = anonymized_text.split()

    src_doc = pymupdf.open(input_pdf)

    # Collect every word with its page index and bounding box
    # get_text("words") -> (x0, y0, x1, y1, word, block_no, line_no, word_no)
    all_words: list[tuple[int, pymupdf.Rect, str]] = []
    for page_idx, page in enumerate(src_doc):
        for w in page.get_text("words"):
            all_words.append((page_idx, pymupdf.Rect(w[0], w[1], w[2], w[3]), w[4]))

    orig_texts = [w[2] for w in all_words]

    matcher = SequenceMatcher(None, orig_texts, anon_words, autojunk=False)

    # replace_at[i] = new text to write at word i (may be multi-word collapsed into one rect)
    # skip contains word indices whose rect should just be blanked (tail of a multi-word orig span)
    replace_at: dict[int, str] = {}
    skip: set[int] = set()

    for op, i1, i2, j1, j2 in matcher.get_opcodes():
        if op == "replace":
            replace_at[i1] = " ".join(anon_words[j1:j2])
            for i in range(i1 + 1, i2):
                skip.add(i)
        elif op == "delete":
            replace_at[i1] = ""
            for i in range(i1 + 1, i2):
                skip.add(i)

    out_doc = pymupdf.open()

    # First pass: create all output pages with rasterized backgrounds
    for page_idx, src_page in enumerate(src_doc):
        page_rect = src_page.rect
        pixmap = src_page.get_pixmap(matrix=pymupdf.Matrix(2, 2), alpha=False)
        new_page = out_doc.new_page(width=page_rect.width, height=page_rect.height)
        new_page.insert_image(page_rect, pixmap=pixmap, overlay=False)

    # Second pass: apply word-level replacements
    for word_idx, (page_idx, rect, _) in enumerate(all_words):
        if word_idx not in replace_at and word_idx not in skip:
            continue

        src_page = src_doc[page_idx]
        new_page = out_doc[page_idx]

        if word_idx in skip:
            new_page.draw_rect(rect, color=None, fill=(1, 1, 1))
            continue

        new_text = replace_at[word_idx]
        fontsize, fontname, text_color = _span_style_at(src_page, rect)
        new_page.draw_rect(rect, color=None, fill=(1, 1, 1))
        if new_text:
            new_page.insert_textbox(
                rect,
                new_text,
                fontsize=fontsize,
                fontname=fontname,
                color=text_color,
                align=pymupdf.TEXT_ALIGN_LEFT,
            )

    src_doc.close()
    out_doc.save(output_pdf)
    out_doc.close()


# ---------------------------------------------------------------------------
# LangGraph anonymization pipeline
# ---------------------------------------------------------------------------

class AnonState(TypedDict):
    current_text: str
    input_pdf: str
    output_path: str


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


def node_save_pdf(state: AnonState) -> AnonState:
    print("[PDF] Building anonymized PDF from scratch...")
    _build_pdf_from_scratch(state["current_text"], state["input_pdf"], state["output_path"])
    print(f"[PDF] Saved to: {state['output_path']}")
    return state


_graph = StateGraph(AnonState)
_graph.add_node("names", node_names)
_graph.add_node("gendered_nouns", node_gendered_nouns)
_graph.add_node("pronouns", node_pronouns)
_graph.add_node("family_status", node_family_status)
_graph.add_node("life_events", node_life_events)
_graph.add_node("save_pdf", node_save_pdf)

_graph.add_edge(START, "names")
_graph.add_edge("names", "gendered_nouns")
_graph.add_edge("gendered_nouns", "pronouns")
_graph.add_edge("pronouns", "family_status")
_graph.add_edge("family_status", "life_events")
_graph.add_edge("life_events", "save_pdf")
_graph.add_edge("save_pdf", END)

anonymization_pipeline = _graph.compile()


def anonymize_pdf(input_pdf: str, output_pdf: str) -> str:
    """Run the full 5-agent anonymization pipeline and save the result as a new PDF.

    Returns the final anonymized text.
    """
    cv_text = extract_pdf_text(input_pdf)
    final_state = anonymization_pipeline.invoke({
        "current_text": cv_text,
        "input_pdf": input_pdf,
        "output_path": output_pdf,
    })
    return final_state["current_text"]


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    test_dir = Path(__file__).parent.parent / "test_cvs"
    input_pdf = str(test_dir / "example5.pdf")
    output_pdf = str(test_dir / "example5_anonymized.pdf")

    print("=" * 60)
    print("ORIGINAL CV TEXT")
    print("=" * 60)
    print(extract_pdf_text(input_pdf))

    anonymized = anonymize_pdf(input_pdf, output_pdf)

    print("\n" + "=" * 60)
    print("FINAL ANONYMIZED TEXT")
    print("=" * 60)
    print(anonymized)
