from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.document_loaders import PyPDFLoader
import os
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

load_dotenv()

model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0
)

template = """You are a Senior HR Specialist. Extract information from the CVs below and return a JSON array.

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

parser = JsonOutputParser()

prompt = PromptTemplate.from_template(
    template,
    partial_variables={"format_instructions": parser.get_format_instructions()},
)

chain = prompt | model | parser


def analyze_pdf_paths(paths: list[str]) -> list[dict]:
    """Load PDFs from file paths, analyze with LLM, return list of candidate dicts."""
    texts = []
    for path in paths:
        loader = PyPDFLoader(path)
        pages = loader.load()
        texts.append("\n".join(p.page_content for p in pages))
    cv_text = "\n\n".join(texts)
    result = chain.invoke({"cv_text": cv_text})
    return result if isinstance(result, list) else result.get("candidates", [result])


if __name__ == "__main__":
    from pathlib import Path
    test_dir = Path(__file__).parent.parent / "test_cvs"
    paths = [str(p) for p in test_dir.glob("*.pdf")]
    candidates = analyze_pdf_paths(paths)
    for i, candidate in enumerate(candidates, start=1):
        print(f"Candidate {i}")
        print("-" * 40)
        for key, value in candidate.items():
            if isinstance(value, list):
                print(f"  {key}:")
                for item in value:
                    print(f"    - {item}")
            else:
                print(f"  {key}: {value}")
        print()