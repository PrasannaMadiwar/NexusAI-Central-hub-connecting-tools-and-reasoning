import os
from dotenv import load_dotenv
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.messages import AIMessage

load_dotenv()


class LazyCodeAgent(Runnable):
    """
    Lazy wrapper for Daytona code execution subagent.
    Prevents eager sandbox creation at import time, allocating sandbox resources on demand.
    """
    def __init__(self):
        self._agent = None

    def _init_agent(self):
        if self._agent is not None:
            return self._agent

        try:
            from daytona import Daytona
            from deepagents import create_deep_agent
            from langchain_daytona import DaytonaSandbox
            from langchain_openai import ChatOpenAI

            llm = ChatOpenAI(model="gpt-4o-mini")
            sandbox = Daytona().create()
            backend = DaytonaSandbox(sandbox=sandbox)

            self._agent = create_deep_agent(
                model=llm,
                system_prompt="""
You are a Python Code Execution SubAgent operating inside a secure Daytona sandbox.

Your sole responsibility is to generate, execute, and debug Python code within the sandbox environment.
""",
                backend=backend,
                skills=["./skills"]
            )
            return self._agent
        except Exception as e:
            raise RuntimeError(f"Could not initialize Daytona sandbox: {str(e)}")

    def invoke(self, input, config: RunnableConfig = None, **kwargs):
        try:
            agent = self._init_agent()
            return agent.invoke(input, config=config, **kwargs)
        except Exception as e:
            return {"messages": [AIMessage(content=f"Code execution sandbox unavailable: {str(e)}")]}

    def stream(self, input, config: RunnableConfig = None, **kwargs):
        try:
            agent = self._init_agent()
            yield from agent.stream(input, config=config, **kwargs)
        except Exception as e:
            yield {"messages": [AIMessage(content=f"Code execution sandbox unavailable: {str(e)}")]}


code_agent = LazyCodeAgent()

# Compatibility alias
codeAgent = code_agent
