import os
import json

from typing import Optional, Union
from uuid import uuid4

import asyncio
import asyncpg
from langgraph.graph import StateGraph, END
from langchain_ollama import OllamaLLM
from pydantic import BaseModel, TypeAdapter

import utils.color_print as cp
import utils.json_validator as jv
from schemas.llm_output_schemas import EngineerOutputSchema
# from schemas.json_output_structures import get_engineer_example_json
from prompts.prompt_library import PromptLibrary
from database import log_agent_step

prompt_lib = PromptLibrary()
DB_URL = os.getenv("SUPABASE_DB_URL")
DUMMY_UUID = os.getenv("DUMMY_UUID")

# LangGraph Node
llm = OllamaLLM(model="llama3.2")

# custom port
# llm = OllamaLLM(model="llama3.2", base_url="http://localhost:11434")

# LangGraph State
class EngineerState(BaseModel):
    run_id: str
    cycle_id: int = 0
    code: str
    prompt: Optional[str] = None
    json_spec: Optional[Union[dict, str]] = None
    validated_output: Optional[EngineerOutputSchema] = None
    retry_count: int = 0
    max_retries: int = 3

def engineer_task(state: EngineerState) -> EngineerState:
    cp.log_info('engineer_task() called')
    cp.log_info(f"▶️ Run: {state.run_id} | Cycle: {state.cycle_id}")

    # example_json = get_engineer_example_json()
    # cp.log_debug('example JSON:', example_json)
    
    # prompt = f"""
    #     You are a senior software engineer. Analyze the following code and extract a structured JSON schema with all functions, variables, and their purposes.

    #     Return ONLY valid JSON, no explanations, no extra text.
    #     Example format:
    #     {example_json}

    #     Code:
    #     {state.code}
    # """

    prompt = prompt_lib.build_prompt("engineer", code=state.code)

    response = llm.invoke(prompt)
    cp.log_debug('response from LLM:', response)

    return EngineerState(
        run_id = state.run_id,
        code = state.code,
        prompt = prompt,
        json_spec = response,
        retry_count = state.retry_count,
        max_retries = state.max_retries
    )

def validate_engineer_json(state: EngineerState) -> EngineerState:
    validated, error = jv.validate_llm_output(state.json_spec, EngineerOutputSchema)
    if validated:
        cp.log_info('✅ output is valid JSON')
        asyncio.create_task(
            log_agent_step({
                "cycle_id": "084aad73-5f1d-49f2-b3f8-910d71945ac9", # state.run_id,
                "agent_id": "77f8f395-41c4-4c3f-8ac7-0aa9d7133f3f",
                "llm_model_id": "07b2a463-7d4e-447d-a35b-0f603151a9a5",
                "prompt_id": "53d81c1b-55b8-4dec-9d71-488ab4565efe",
                "step_number": state.retry_count,
                "raw_input": state.prompt,
                "raw_output": state.json_spec,
                "validated_json": state.json_spec,
                "confidence": None,
                "feedback": None,
                "status": "completed"
            }
        ))
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
        cp.log_warn(f'Retrying validation, attempt {state.retry_count}/{state.max_retries}')
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