import os

import uuid
import asyncpg
from dotenv import load_dotenv

import utils.color_print as cp

load_dotenv()

DB_URL = os.getenv("SUPABASE_DB_URL")

async def get_db_conn():
    return await asyncpg.connect(DB_URL)

async def log_agent_step(data: dict):
    
    conn = await get_db_conn()
    await conn.execute("""
        INSERT INTO temp_agent_step (
            project_id, run_id, cycle_id, step_number,
            agent_id, agent_role, agent_desc,
            llm_model_id, llm_model_name, llm_model_temperature, llm_model_top_p,
            prompt_id, prompt_type,
            raw_input, raw_output, validated_json,
            confidence, status, time_taken, file_path
        ) VALUES (
            $1, $2, $3, $4,
            $5, $6, $7,
            $8, $9, $10, $11,
            $12, $13,
            $14, $15, $16,
            $17, $18, $19, $20
        )
    """,    data['project_id'], data['run_id'], data['cycle_id'], data['step_number'],
            data['agent_id'], data['agent_role'], "N/A",
            data['llm_model_id'], data['llm_model_name'], data['llm_model_temperature'], data['llm_model_top_p'],
            data['prompt_id'], data['prompt_type'],
            data['raw_input'], data['raw_output'], data['validated_json'],
            data['confidence'], data['status'], 0, data['file_path'])
    cp.log_info("Agent step logged successfully.")
    await conn.close()

async def fetch_data(query: str):
    conn = await get_db_conn()
    try:
        results = await conn.fetch(query)
        return [
            {k: str(v) if isinstance(v, (uuid.UUID, asyncpg.pgproto.pgproto.UUID)) else v for k, v in dict(row).items()}
            for row in results
        ]
    finally:
        await conn.close()