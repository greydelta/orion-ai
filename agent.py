import os, json

import httpx
from dotenv import load_dotenv
from uuid import uuid4

import utils.color_print as cp
from utils.json_rpc_client import json_rpc_client
from langgraph_pipeline import graph, EngineerState

load_dotenv()

LOCAL_MCP_SERVER_URL = os.getenv("LOCAL_MCP_SERVER_URL")
OLLAMA_URL = os.getenv("OLLAMA_URL")

async def run_engineer_pipeline(file_name="src/App.java"):
    cp.log_info('run_engineer_pipeline() called')
    # async with httpx.AsyncClient(verify=False) as client:
    #     resp = await client.post(LOCAL_MCP_SERVER_URL, json={
    #         "jsonrpc": "2.0",
    #         "method": "get_context",
    #         "params": {},
    #         "id": 1
    #     })
    #     docs = resp.json()["result"]["documents"]

    result = await json_rpc_client("get_context")
    docs = result["documents"]

    # Find file content
    match = next((doc for doc in docs if doc["name"] == file_name), None)
    if not match:
        return {"error": "file not found"}

    # Run through LangGraph
    # initial_state = EngineerState(code=match["content"])
    initial_state = EngineerState(
        run_id = str(uuid4()),
        cycle_id = 0,
        code = match["content"]
    )
    result = graph.invoke(initial_state)

    raw_output = result.get("json_spec", "")
    cp.log_debug("🧠 Raw LLM Output:\n" + raw_output)

    try:
        parsed = json.loads(raw_output)
        functions = parsed.get("functions", [])
        cp.log_info(f"\n🔍 Found {len(functions)} functions:")

        for idx, func in enumerate(functions, start=1):
            cp.log_info(f"Function {idx}:")
            cp.log_info("  Name:", func.get("name"))
            cp.log_info("  Parameters:", ", ".join(func.get("parameters", [])))
            cp.log_info("  Description:", func.get("description"))
            cp.log_info()
    except Exception as e:
        cp.log_error(f"❌ Failed to parse LLM output: {e}")
        return {"error": str(e)}

    # return parsed  #
    return result.get("json_spec", "No output")

async def list_files():
    cp.log_info('list_files() called')
    result = await json_rpc_client("list_files")
    return result["files"]

async def get_prompt_for_file(filename, target_language="Python"):
    cp.log_info('get_prompt_for_file() called')
    result = await json_rpc_client("run", {"filename": filename, "target_language": target_language})
    return result["prompt"]

async def get_context():
    cp.log_info('get_context() called')
    result = await json_rpc_client("get_context")
    return result["documents"]

# ^ manual query
async def query_ollama(prompt):
    cp.log_info('query_ollama() called')
    async with httpx.AsyncClient(timeout=None, verify=False) as client:
        resp = await client.post(f"{OLLAMA_URL}/api/generate", json={
            "model": "llama3.2",
            "prompt": prompt,
            "stream": False
        })
        cp.log_debug("🔎 Full response from Ollama: ", resp)
        return resp.json()["response"]

# async def run_agent():
#     docs = await get_context()
#     prompt = "Translate the following Java code to Python:\n\n" + docs[0]["content"]
#     response = await query_ollama(prompt)
#     log_info("\n🔁 Model Response:\n", response)

async def run_agent(file_name="Example.java", target_lang="Python"):
    cp.log_info('run_agent() called')
    docs = await get_context()

    # Find the specific file
    target_doc = next((doc for doc in docs if doc["name"] == file_name), None)
    if not target_doc:
        cp.log_error(f"❌ File '{file_name}' not found.")
        return

    prompt = f"Translate the following Java code to {target_lang}:\n\n{target_doc['content']}"

    async with httpx.AsyncClient(timeout=None, verify=False) as client:
        resp = await client.post(f"{OLLAMA_URL}/api/generate", json={
            "model": "llama3.2",
            "prompt": prompt,
            "stream": False
        })
        response = resp.json()["response"]
        cp.log_debug(f"\n🔁 Model Response:\n\n{response}")

if __name__ == "__main__":
    import asyncio
    # asyncio.run(run_agent(file_name="src/App.java", target_lang="Python"))
    asyncio.run(run_engineer_pipeline(file_name="src/App.java"))