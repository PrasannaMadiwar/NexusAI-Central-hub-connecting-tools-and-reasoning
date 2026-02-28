from langchain_groq import ChatGroq 
from dotenv import load_dotenv

from daytona import Daytona
from deepagents import create_deep_agent
from langchain_daytona import DaytonaSandbox
load_dotenv()

llm = ChatGroq(model="openai/gpt-oss-120b")
sandbox = Daytona().create()
backend = DaytonaSandbox(sandbox=sandbox)



codeAgent = create_deep_agent(
    model=llm,
    system_prompt="""
You are a Python Code Execution SubAgent operating inside a secure Daytona sandbox.

Your sole responsibility is to generate, execute, and debug Python code within the sandbox environment.
""",
    backend=backend,
    skills=["./skills"]
)
