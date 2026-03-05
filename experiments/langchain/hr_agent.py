from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pdfToText import docs

load_dotenv()

cv_text = "\n\n".join(doc.page_content for doc in docs)

# Configure model
model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0
)

template = """You are a Senior HR Specialist with 15 years of experience in recruiting. You analyze CVs using the available tools. Get the condidate's personal information (name, email, phone, location) and skills (technologies, competencies) from the CV.

Here are all the candidates' CVs which a emthy line separating them:

{cv_text}

{format_instructions}
"""

parser = JsonOutputParser()

prompt = PromptTemplate.from_template(
    template,
    partial_variables={"format_instructions": parser.get_format_instructions()},
)

chain = prompt | model | parser

result = chain.invoke({"cv_text": cv_text})
candidates = result if isinstance(result, list) else result.get("candidates", [result])
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