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
from prompts.prompt_library import PromptLibrary
from database import log_agent_step

prompt_lib = PromptLibrary()
DB_URL = os.getenv("SUPABASE_DB_URL")

# LangGraph Node
llm = OllamaLLM(model="llama3.2")

# custom port
# llm = OllamaLLM(model="llama3.2", base_url="http://localhost:11434")

# LangGraph State
class EngineerState(BaseModel):
    project_id: str = "alpha"
    run_id: str
    cycle_id: int = 0
    agent: object = None 
    model: object = None
    code: str
    prompt: object = None
    json_spec: Optional[Union[dict, str]] = None
    validated_output: Optional[EngineerOutputSchema] = None
    retry_count: int = 0
    max_retries: int = 3

def engineer_task(state: EngineerState) -> EngineerState:
    prompt_type = "code_extraction"
    cp.log_info('engineer_task() called')
    cp.log_info(f"▶️ Run: {state.run_id} | Cycle: {state.cycle_id}")

    prompt, prompt_id = prompt_lib.build_prompt("engineer", prompt_type, code=state.code)
    role, role_id = prompt_lib.get_role_details("engineer", prompt_type)

    response = llm.invoke(prompt)
    cp.log_debug('response from LLM:', response)

    return EngineerState(
        run_id = state.run_id,
        code = state.code,
        prompt = { "id": prompt_id, "type": prompt_type, "input": prompt },
        model = { "id": "1", "name": "llama3.2" },
        agent = { "id": role_id, "role": role },
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
                "project_id": "alpha",
                "run_id": state.run_id,
                "cycle_id": str(state.retry_count + 1),
                "step_number": state.retry_count + 1,

                "agent_id": state.agent["id"],
                "agent_role": state.agent["role"],
                "llm_model_id": state.model["id"],
                "llm_model_name": state.model["name"],
                "prompt_id": state.prompt["id"],
                "prompt_type": state.prompt["type"],
                "raw_input": state.prompt["input"],

                "raw_output": state.json_spec,
                "validated_json": state.json_spec,
                "confidence": None,
                "status": "passed"
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