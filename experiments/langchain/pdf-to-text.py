from pypdf import PdfReader

with open("example.pdf", "rb") as file:
    reader = PdfReader(file)
    number_of_pages = len(reader.pages)

    ptdf_text = ""

    for page in reader.pages:
        text = page.extract_text()
        ptdf_text += text
        
print(ptdf_text)