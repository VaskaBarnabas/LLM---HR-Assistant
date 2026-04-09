from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / "backend" / ".env")

from experiments.langchain.hr_workflow import anonymize_pdf, extract_pdf_text

INPUT_PDF = str(Path(__file__).parent / "test_cvs" / "example5.pdf")
OUTPUT_PDF = str(Path(__file__).parent / "test_cvs" / "example5_anonymized.pdf")

print("=" * 60)
print("ORIGINAL CV TEXT")
print("=" * 60)
print(extract_pdf_text(INPUT_PDF))

anonymized = anonymize_pdf(INPUT_PDF, OUTPUT_PDF)

print("\n" + "=" * 60)
print("FINAL ANONYMIZED TEXT")
print("=" * 60)
print(anonymized)
