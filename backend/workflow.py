from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END

from experiments.langchain.hr_workflow import analyze_pdf_paths

#State
class State(TypedDict):
    texts: list[str]

#Nodes

# This node takes a list of PDF file paths, extracts text from each, and returns a list of strings.
def pdf_to_text_node(paths: list[str]) -> State:
    cv_texts = analyze_pdf_paths(paths)
    return {"texts": cv_texts}

def text_to_vectordb_node(state: State) -> State:
    
    return state