from pypdf import PdfReader

def extract_pdf_text(pdf_name):
    """Extract text from all pages of a PDF file."""
    with open(pdf_name, "rb") as file:
        reader = PdfReader(file)

        ptdf_text = ""

        for page in reader.pages:
            text = page.extract_text()
            ptdf_text += text
        
    return ptdf_text