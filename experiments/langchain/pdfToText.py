import re
from pathlib import Path
from annotated_types import doc
from langchain_community.document_loaders import FileSystemBlobLoader
from langchain_community.document_loaders.generic import GenericLoader
from langchain_community.document_loaders.parsers import PyPDFParser
from pypdf import PdfReader


def _fix_spaced_chars(text):
    """Collapse 'H e l l o' → 'Hello' caused by certain PDF font encodings."""
    return re.sub(
        r'(?<!\w)([A-Za-zÀ-ÿ\d] )+[A-Za-zÀ-ÿ\d](?!\w)',
        lambda m: m.group().replace(' ', ''),
        text
    )

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

    return _fix_spaced_chars(ptdf_text)