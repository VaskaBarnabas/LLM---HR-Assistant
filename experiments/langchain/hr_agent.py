import os
from dotenv import load_dotenv
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import HumanMessage
from pdfToText import extract_pdf_text

load_dotenv()

pdf_text = extract_pdf_text("example_cv.pdf")

# Embed the CV text in the system prompt so every call has access to it
SYSTEM_PROMPT = f"""You are a Senior HR Specialist with 15 years of experience in recruiting. You analyze CVs using the available tools.
You have access to two tools:
- get_personal_information: extracts the candidate's personal details (name, email, phone, location)
- get_skills: extracts the candidate's skills and competencies

Here is the candidate's CV:
---
{pdf_text}
---

Use the tools to extract the required information, then answer the user's question."""


# Tools use pdf_text from the enclosing scope — no need to pass it every time
@tool
def get_personal_information() -> str:
    """Extract name, email, phone, and location from the candidate's CV."""
    return pdf_text


@tool
def get_skills() -> str:
    """Extract skills, technologies, and competencies from the candidate's CV."""
    return pdf_text


# Configure model
model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0
)

# Set up memory
checkpointer = InMemorySaver()

# Create agent
agent = create_agent(
    model=model,
    tools=[get_personal_information, get_skills],
    system_prompt=SYSTEM_PROMPT,
    checkpointer=checkpointer
)

config = {"configurable": {"thread_id": "1"}}

# Now every invoke is a simple question — no need to pass pdf_text
response = agent.invoke(
    {"messages": [HumanMessage(content="What are the candidate's skills and personal information? Return as JSON.")]},
    config=config
)
print(response["messages"][-1].content)
