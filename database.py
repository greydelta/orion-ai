import os

import uuid
import asyncpg
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("SUPABASE_DB_URL")

async def get_db_conn():
    return await asyncpg.connect(DB_URL)

async def log_agent_step(data: dict):
    conn = await get_db_conn()
    await conn.execute("""
        INSERT INTO agent_step (
            cycle_id, agent_id, llm_model_id, prompt_id,
            step_number, raw_input, raw_output,
            validated_json, confidence, feedback, status
        ) VALUES (
            $1, $2, $3, $4,
            $5, $6, $7,
            $8, $9, $10, $11
        )
    """, data['cycle_id'], data['agent_id'], data['llm_model_id'], data['prompt_id'],
         data['step_number'], data['raw_input'], data['raw_output'],
         data['validated_json'], data['confidence'], data['feedback'], data['status'])
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