from langchain_community.document_loaders import PyPDFLoader

def analyze_pdf_paths(paths: list[str]) -> list[str]:
    """Load PDFs from file paths, extract text, and return a list of texts."""
    texts = []
    for path in paths:
        loader = PyPDFLoader(path)
        pages = loader.load()
        texts.append("\n".join(p.page_content for p in pages))
    return texts
