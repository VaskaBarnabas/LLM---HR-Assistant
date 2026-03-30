import re
from pathlib import Path
import pymupdf

from dotenv import load_dotenv
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict

from backend.utils.pdfToText import extract_pdf_text

load_dotenv(Path(__file__).parent.parent / "backend" / ".env")

INPUT_PDF = str(Path(__file__).parent / "test_cvs" / "example5.pdf")
OUTPUT_PDF = str(Path(__file__).parent / "test_cvs" / "example5_anonymized.pdf")


# --- State ---

class AnonState(TypedDict):
    cv_text: str
    replacements: list[dict]
    output_path: str


# --- Tools ---

@tool
def find_pronoun_replacements(text: str) -> list[dict]:
    """Find gendered pronouns in the CV text and return a list of replacements.
    Each replacement is {"original": str, "replacement": str}."""
    pronoun_map = {
        " she ": " they ",
  #      " he ": " they ",
        " her ": " their ",
        " his ": " their ",
        " him ": " them ",
        " herself ": " themselves ",
        " himself ": " themselves ",
        "She ": "They ",
   #     "He ": "They ",
        "Her ": "Their ",
        "His ": "Their ",
        "Him ": "Them ",
    }
    replacements = []
    for original, replacement in pronoun_map.items():
        if original in text:
            replacements.append({
                "original": original,
                "replacement": replacement,
            })
    return replacements


@tool
def find_title_replacements(text: str) -> list[dict]:
    """Find gendered honorific titles (Mr., Mrs., Ms., Miss, Sir, Madam) and return
    neutral replacements. Each replacement is {"original": str, "replacement": str}."""
    title_map = {
        "Mrs.": "Mx.",
        "Mr.": "Mx.",
        "Ms.": "Mx.",
        "Miss ": "Mx. ",
        "Sir ": "Mx. ",
        "Madam ": "Mx. ",
    }
    replacements = []
    for original, replacement in title_map.items():
        if original in text:
            replacements.append({
                "original": original,
                "replacement": replacement,
            })
    return replacements


@tool
def find_gendered_word_replacements(text: str) -> list[dict]:
    """Find gendered job titles and other gendered words in the CV text and return
    gender-neutral replacements. Each replacement is {"original": str, "replacement": str}."""
    word_map = {
        "chairmen": "chairpeople",
        "chairwomen": "chairpeople",
        "chairman": "chairperson",
        "chairwoman": "chairperson",
        "businessmen": "businesspeople",
        "businesswomen": "businesspeople",
        "businessman": "businessperson",
        "businesswoman": "businessperson",
        "policemen": "police officers",
        "policewomen": "police officers",
        "policeman": "police officer",
        "policewoman": "police officer",
        "firemen": "firefighters",
        "fireman": "firefighter",
        "stewardesses": "flight attendants",
        "stewardess": "flight attendant",
        "manpower": "workforce",
        "mankind": "humankind",
        "man-hours": "person-hours",
        "salesmen": "salespeople",
        "saleswomen": "salespeople",
        "salesman": "salesperson",
        "saleswoman": "salesperson",
        "spokesmen": "spokespeople",
        "spokeswomen": "spokespeople",
        "spokesman": "spokesperson",
        "spokeswoman": "spokesperson",
        "actresses": "actors",
        "actress": "actor",
        "waitresses": "servers",
        "waitress": "server",
        "waiters": "servers",
        "waiter": "server",
        "landlords": "property owners",
        "landladies": "property owners",
        "landlord": "property owner",
        "landlady": "property owner",
        "foremen": "supervisors",
        "foreman": "supervisor",
        "forewoman": "supervisor",
        "workmen": "workers",
        "workman": "worker",
        "workwoman": "worker",
    }
    replacements = []
    for original, replacement in word_map.items():
        if re.search(r"\b" + re.escape(original) + r"\b", text, re.IGNORECASE):
            replacements.append({"original": original, "replacement": replacement})
    return replacements


@tool
def apply_replacements_to_pdf(
    replacements: list[dict],
    output_path: str,
) -> str:
    """Copy the original PDF and apply text replacements using PyMuPDF redaction,
    preserving the original formatting. Each replacement must be {"original": str, "replacement": str}.
    Returns the output path on success."""
    def get_text_style_at(page, rect):
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
                        return span["size"], fontname
        return 10, "helv"

    doc = pymupdf.open(INPUT_PDF)

    for page in doc:
        for item in replacements:
            instances = page.search_for(item["original"])
            for rect in instances:
                fontsize, fontname = get_text_style_at(page, rect)
                page.add_redact_annot(rect, item["replacement"], fontsize=fontsize, fontname=fontname)
        page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE)

    doc.save(output_path)
    doc.close()
    return output_path


# --- Graph nodes ---

def pronouns_node(state: AnonState) -> AnonState:
    new = find_pronoun_replacements.invoke({"text": state["cv_text"]})
    return {"replacements": state["replacements"] + new}


def titles_node(state: AnonState) -> AnonState:
    new = find_title_replacements.invoke({"text": state["cv_text"]})
    return {"replacements": state["replacements"] + new}


def words_node(state: AnonState) -> AnonState:
    new = find_gendered_word_replacements.invoke({"text": state["cv_text"]})
    return {"replacements": state["replacements"] + new}


def save_pdf_node(state: AnonState) -> AnonState:
    apply_replacements_to_pdf.invoke({
        "replacements": state["replacements"],
        "output_path": state["output_path"],
    })
    return state


# --- Graph ---

graph = StateGraph(AnonState)

graph.add_node("pronouns", pronouns_node)
graph.add_node("titles", titles_node)
graph.add_node("words", words_node)
graph.add_node("save_pdf", save_pdf_node)

graph.add_edge(START, "pronouns")
graph.add_edge("pronouns", "titles")
graph.add_edge("titles", "words")
graph.add_edge("words", "save_pdf")
graph.add_edge("save_pdf", END)

pipeline = graph.compile()

# --- Run ---

cv_text = extract_pdf_text(Path(__file__).parent / "test_cvs" / "example5.pdf")

print("=" * 60)
print("ORIGINAL CV")
print("=" * 60)
print(cv_text)

final_state = pipeline.invoke({
    "cv_text": cv_text,
    "replacements": [],
    "output_path": OUTPUT_PDF,
})

anonymized_text = extract_pdf_text(Path(__file__).parent / "test_cvs" / "example5_anonymized.pdf")

print("\n" + "=" * 60)
print("ANONYMIZED CV")
print("=" * 60)
print(anonymized_text)


print("\n" + "=" * 60)
print("REPLACEMENTS APPLIED")
print("=" * 60)
for item in final_state["replacements"]:
    print(f"  '{item['original']}' -> '{item['replacement']}'")