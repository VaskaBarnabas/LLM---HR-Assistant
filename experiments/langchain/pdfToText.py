# from pypdf import PdfReader

# def extract_pdf_text(pdf_name):
#     """Extract text from all pages of a PDF file."""
#     with open(pdf_name, "rb") as file:
#         reader = PdfReader(file)

#         ptdf_text = ""

#         for page in reader.pages:
#             text = page.extract_text()
#             ptdf_text += text

#     return ptdf_text

from pathlib import Path
from annotated_types import doc
from langchain_community.document_loaders import FileSystemBlobLoader
from langchain_community.document_loaders.generic import GenericLoader
from langchain_community.document_loaders.parsers import PyPDFParser

loader = GenericLoader(
    blob_loader=FileSystemBlobLoader(
        path=Path(__file__).parent.parent / "test_cvs",
        glob="*.pdf",
    ),
    blob_parser=PyPDFParser(),
)
docs = loader.load()
#for doc in docs:
#   print(doc.page_content)
#    print(doc.metadata)
#    print()