from typing import Optional, Union

from langgraph.graph import StateGraph, END
from langchain_ollama import OllamaLLM
from pydantic import BaseModel

import utils.color_print as cp

# LangGraph State
class EngineerState(BaseModel):
    code: str
    json_spec: Optional[Union[dict, str]] = None

# LangGraph Node
llm = OllamaLLM(model="llama3.2")

# custom port
# llm = OllamaLLM(model="llama3.2", base_url="http://localhost:11434")

def engineer_task(state: EngineerState) -> EngineerState:
    cp.log_info('engineer_task() called')
    prompt = f"""
        You are a senior software engineer. Analyze the following code and extract a structured JSON schema with all functions, classes, and their purposes.

        Respond only in this format:
        {{
        "functions": [
            {{
            "name": "...",
            "parameters": ["..."],
            "description": "..."
            }}
        ]
        }}

        Code:
        {state.code}
    """
    response = llm.invoke(prompt)
    return EngineerState(code=state.code, json_spec=response)

# LangGraph Compiler
builder = StateGraph(EngineerState)
builder.add_node("engineer", engineer_task)
builder.set_entry_point("engineer")
builder.set_finish_point("engineer")

graph = builder.compile()