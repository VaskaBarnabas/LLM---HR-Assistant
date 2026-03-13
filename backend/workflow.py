import os
from pathlib import Path
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from backend.chromaClient import add_documents
from backend.utils.path_analizer import analyze_pdf_paths

load_dotenv(Path(__file__).parent / ".env")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0
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


# State
class State(TypedDict):
    paths: list[str]
    texts: list[str]
    candidates: list[dict]


# Nodes

# This node takes a list of PDF file paths, extracts text from each, and returns a list of strings.
def pdf_to_text_node(state: State) -> State:
    cv_texts = analyze_pdf_paths(state["paths"])
    return {"texts": cv_texts}

# This node takes a list of text documents and adds them to the ChromaDB collection.
def text_to_vectordb_node(state: State) -> State:
    add_documents(state["texts"])
    return state

# This node takes a list of CV texts, analyzes each with the LLM, and returns structured candidate data.
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

workflow.add_node("pdf_to_text", pdf_to_text_node)
workflow.add_node("text_to_vectordb", text_to_vectordb_node)
workflow.add_node("analyze_cv", analyze_cv_node)
workflow.add_node("print_candidates", print_candidates_node)

workflow.add_edge(START, "pdf_to_text")
workflow.add_edge("pdf_to_text", "text_to_vectordb")
workflow.add_edge("text_to_vectordb", "analyze_cv")
workflow.add_edge("analyze_cv", "print_candidates")
workflow.add_edge("print_candidates", END)

chain = workflow.compile()
