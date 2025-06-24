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
    project_id: str = "beta"
    run_id: str
    cycle_id: int = 0
    
    step_number: int = 0
    retry_count: int = 0
    max_retries: int = 3
    
    agent: Optional[dict] = None
    model: Optional[dict] = None

    code: str
    prompt: Optional[dict] = None
    json_spec: Optional[Union[dict, str]] = None
    validated_output: Optional[EngineerOutputSchema] = None
    reviewer_feedback: Optional[str] = None

def engineer_task(state: EngineerState) -> EngineerState:
    cp.log_info('engineer_task() called')
    cp.log_info(f"▶️ Run: {state.run_id} | Cycle: {state.cycle_id} | Step: {state.step_number}")
    
    prompt_type = "code_to_json_after_feedback" if state.reviewer_feedback else "code_to_json"

    prompt, prompt_id = prompt_lib.build_prompt("engineer", prompt_type, code=state.code, feedback=state.reviewer_feedback)
    role, role_id = prompt_lib.get_role_details("engineer", prompt_type)

    response = llm.invoke(prompt)
    cp.log_debug('response from LLM:', response)

    return state.model_copy(update={
        "prompt": {"id": prompt_id, "type": prompt_type, "input": prompt},
        "model": {"id": "1", "name": "llama3.2"},
        "agent": {"id": role_id, "role": role},
        "json_spec": response,
        "step_number": 0,
        "reviewer_feedback": None
    })

def validate_engineer_json(state: EngineerState) -> EngineerState:
    validated, error = jv.validate_llm_output(state.json_spec, EngineerOutputSchema)
    if validated:
        cp.log_info('✅ output is valid JSON')
        asyncio.create_task(
            log_agent_step({
                "project_id": state.project_id,
                "run_id": state.run_id,
                "cycle_id": str(state.cycle_id),
                "step_number": state.step_number,

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
                "status": "generated"
            }
        ))
        return state.model_copy(update={"validated_output": validated, "step_number": 0})
    else:
        cp.log_warn(f"❌ invalid JSON detected. Retry step {state.step_number + 1}/{state.max_retries}")
        return state.model_copy(update={"step_number": state.step_number + 1})

def product_manager_task(state: EngineerState) -> EngineerState:
    cp.log_info("🔍 product_manager_task() called")
    prompt_type = "json_review"

    prompt, prompt_id = prompt_lib.build_prompt("product_manager", prompt_type, code=state.code, json_output=state.json_spec)
    role, role_id = prompt_lib.get_role_details("product_manager", prompt_type)

    feedback = llm.invoke(prompt)
    cp.log_debug("📝 Reviewer feedback:", feedback)

    updated_state = state.model_copy(update={
        "prompt": {"id": prompt_id, "type": prompt_type, "input": prompt},
        "model": {"id": "1", "name": "llama3.2"},
        "agent": {"id": role_id, "role": role}
    })

    cp.log_debug("feedback:", feedback.lower())

    if "no issue" in feedback.lower():
        cp.log_info("✅ Reviewer approved output.")
        asyncio.create_task(log_agent_step({
            "project_id": state.project_id,
            "run_id": state.run_id,
            "cycle_id": str(state.cycle_id),
            "step_number": state.step_number,
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
        }))
        return state

    else:
        cp.log_warn("❌ Reviewer suggests rework based on quality.")
        asyncio.create_task(
            log_agent_step({
                "project_id": state.project_id,
                "run_id": state.run_id,
                "cycle_id": str(state.cycle_id),
                "step_number": state.step_number,

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
                "status": "failed"
            }
        ))

        return updated_state.model_copy(update={
            "reviewer_feedback": feedback,
            "cycle_id": state.cycle_id + 1,
            "validated_output": None
        })

def route_validation_result(state: EngineerState) -> str:
    if state.validated_output:
        cp.log_info('Proceeding to review.')
        return "review"
    elif state.step_number >= state.max_retries:
        cp.log_error(f'⛔ Terminating after {state.step_number} retries.')
        return END
    else:
        cp.log_info('Returning to engineer.')
        return "engineer"

def route_reviewer_result(state: EngineerState) -> str:
    if state.validated_output:
        cp.log_info("✅ Validation successful, proceeding to end state.")
        return END
    else:
        cp.log_info("Returning to engineer.")
        return "engineer"

# LangGraph Compiler
builder = StateGraph(EngineerState)

builder.add_node("engineer", engineer_task)
builder.add_node("validate", validate_engineer_json)
builder.add_node("review", product_manager_task)

builder.set_entry_point("engineer")

# Branch to validation
builder.add_edge("engineer", "validate")

builder.add_conditional_edges(
    "validate",
    path=route_validation_result,
    path_map={
        "review": "review",
        "engineer": "engineer",
        END: END
    }
)

builder.add_conditional_edges(
    "review",
    path=route_reviewer_result,
    path_map={
        "engineer": "engineer",
        END: END
    }
)

graph = builder.compile()