from pathlib import Path
from annotated_types import doc
from langchain_community.document_loaders import FileSystemBlobLoader
from langchain_community.document_loaders.generic import GenericLoader
from langchain_community.document_loaders.parsers import PyPDFParser
from pypdf import PdfReader

loader = GenericLoader(
    blob_loader=FileSystemBlobLoader(
        path=Path(__file__).parent.parent / "test_cvs",
        glob="*.pdf",
    ),
    blob_parser=PyPDFParser(),
)
docs = loader.load()



# Alternative method using PyPDF directly for the chromaDB collection
def extract_pdf_text(pdf_name):
    """Extract text from all pages of a PDF file in the test_cvs folder."""
    pdf_path = Path(__file__).parent.parent / "test_cvs" / pdf_name
    with open(pdf_path, "rb") as file:
        reader = PdfReader(file)

        ptdf_text = ""

        for page in reader.pages:
            text = page.extract_text()
            ptdf_text += text
        
    return ptdf_text