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