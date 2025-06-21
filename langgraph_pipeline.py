import json

from typing import Optional, Union
from uuid import uuid4

from langgraph.graph import StateGraph, END
from langchain_ollama import OllamaLLM
from pydantic import BaseModel, TypeAdapter

import utils.color_print as cp
import utils.json_validator as jv
from schemas.llm_output_schemas import EngineerOutputSchema
from schemas.json_output_structures import get_engineer_example_json

# LangGraph State
class EngineerState(BaseModel):
    run_id: str
    cycle_id: int = 0
    code: str
    json_spec: Optional[Union[dict, str]] = None
    validated_output: Optional[EngineerOutputSchema] = None
    retry_count: int = 0
    max_retries: int = 3

# LangGraph Node
llm = OllamaLLM(model="llama3.2")

# custom port
# llm = OllamaLLM(model="llama3.2", base_url="http://localhost:11434")

def engineer_task(state: EngineerState) -> EngineerState:
    cp.log_info('engineer_task() called')
    cp.log_info(f"▶️ Run: {state.run_id} | Cycle: {state.cycle_id}")

    example_json = get_engineer_example_json()
    # cp.log_debug('example JSON:', example_json)
    
    prompt = f"""
        You are a senior software engineer. Analyze the following code and extract a structured JSON schema with all functions, variables, and their purposes.

        Return ONLY valid JSON, no explanations, no extra text.
        Example format:
        {example_json}

        Code:
        {state.code}
    """

    # prompt = f"""
    #     You are a senior software engineer. Analyze the following code and extract a structured JSON schema with all functions, classes, and their purposes.

    #     Return ONLY valid JSON, no explanations, no extra text.
    #     {{
    #     "functions": [
    #         {{
    #         "name": "...",
    #         "parameters": ["..."],
    #         "description": "..."
    #         }}
    #     ]
    #     }}

    #     Code:
    #     {state.code}
    # """
    response = llm.invoke(prompt)
    cp.log_debug('response from LLM:', response)

    return EngineerState(
        run_id = state.run_id,
        code = state.code,
        json_spec = response,
        retry_count = state.retry_count,
        max_retries = state.max_retries
    )

def validate_engineer_json(state: EngineerState) -> EngineerState:
    validated, error = jv.validate_llm_output(state.json_spec, EngineerOutputSchema)
    if validated:
        cp.log_info('✅ output is valid JSON')
        return EngineerState(
            run_id = state.run_id,
            code = state.code,
            validated_output = validated
        )
    else:
        new_retry = state.retry_count + 1
        cp.log_warn(f'❌ invalid JSON detected. Retry attempt {new_retry}/{state.max_retries}')
        return EngineerState(
            run_id = state.run_id,
            code = state.code,
            retry_count = new_retry
        )

def route_validation_result(state: EngineerState) -> str:
    if state.validated_output:
        cp.log_info('✅ Validation successful, proceeding to end state.')
        return END
    elif state.retry_count >= state.max_retries:
        cp.log_error(f'⛔ Terminating after {state.retry_count} retries.')
        return END
    else:
        cp.log_warn(f'Retrying validation, attempt {state.retry_count + 1}/{state.max_retries}')
        return "invalid"

# LangGraph Compiler
builder = StateGraph(EngineerState)

builder.add_node("engineer", engineer_task)
builder.add_node("validate", validate_engineer_json)

builder.set_entry_point("engineer")

# Branch to validation
builder.add_edge("engineer", "validate")

# Conditional retry based on validation result
builder.add_conditional_edges(
    "validate",
    path=route_validation_result,
    path_map={
        END: END,
        "invalid": "engineer"
    }
)

graph = builder.compile()