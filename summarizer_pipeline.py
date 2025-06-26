import os
import json

from typing import Optional, Union

import asyncio
import asyncpg
import streamlit as st
from langgraph.graph import StateGraph, END
from langchain_ollama import OllamaLLM
from pydantic import BaseModel, TypeAdapter

import utils.color_print as cp
from llm_provider import build_llm
from langgraph_pipeline import ConversionWorkflowState
from prompts.prompt_library import PromptLibrary
from database import log_agent_step, fetch_data
from utils.llm_output_parser import parse_llm_response

prompt_lib = PromptLibrary()
DB_URL = os.getenv("SUPABASE_DB_URL")

# llm = OllamaLLM(model="llama3.2")

# custom port
# llm = OllamaLLM(model="llama3.2", base_url="http://localhost:11434")

async def summarizer_task(state: ConversionWorkflowState) -> ConversionWorkflowState:
    cp.log_info("🧠 summarizer_task() called")

    async def load_validated_jsons(run_id: str) -> list[dict]:
        query = f"""
            SELECT validated_json
            FROM temp_agent_step
            WHERE run_id = '{run_id}'
              AND status = 'generated'
              AND validated_json IS NOT NULL
            ORDER BY file_path
        """
        return await fetch_data(query)

    json_rows = await(load_validated_jsons(state.run_id))
    json_list = [row["validated_json"] for row in json_rows if row.get("validated_json")]

    if not json_list:
        cp.log_warn("⚠️ No validated JSON specs found.")
        return state

    prompt_type = "json_to_user_story"
    prompt, prompt_id = prompt_lib.build_prompt("architect", prompt_type, json_list=json_list)
    role, role_id = prompt_lib.get_role_details("architect", prompt_type)

    model2_config = state.model1_config

    # override temperature and top_p for reviewer
    model2_config["temperature"] = 0.3
    model2_config["top_p"] = 1.0

    llm = build_llm(model2_config["provider"], model2_config["model_name"], model2_config["api_key"], model2_config["temperature"], model2_config["top_p"])
    response = await llm.ainvoke(prompt)
    response_parsed = parse_llm_response(response)

    cp.log_debug("📄 Summary User Stories:", response_parsed)

    await log_agent_step({
        "project_id": state.project_id,
        "run_id": state.run_id,
        "cycle_id": str(state.cycle_id),
        "step_number": state.step_number,
        "agent_id": role_id,
        "agent_role": role,
        "llm_model_id": "1",
        "llm_model_name": model2_config["model_name"],
        "llm_model_temperature": 0.3,
        "llm_model_top_p": 1.0,
        "prompt_id": prompt_id,
        "prompt_type": prompt_type,
        "raw_input": prompt,
        "raw_output": (
                response_parsed.json_spec if isinstance(response_parsed.json_spec, str)
                else json.dumps(response_parsed.json_spec)
            ),
        "validated_json": json.dumps(response_parsed.model_dump()),
        "confidence": None,
        "file_path": None,
        "status": "summarized",
    })

    return state.model_copy(update={
        "agent": {"id": role_id, "role": role},
        "model": {"id": "1", "name": model2_config["model_name"], "temperature": model2_config["temperature"], "top_p": model2_config["top_p"]},
        "prompt": {"id": prompt_id, "type": prompt_type, "input": prompt},
        "json_spec": response_parsed
    })

builder = StateGraph(ConversionWorkflowState)
builder.add_node("summarizer", summarizer_task)
builder.set_entry_point("summarizer")
builder.add_edge("summarizer", END)

summarizerWorkflow = builder.compile()
