import json

import httpx
import streamlit as st
from dotenv import load_dotenv
from typing import Optional, Union
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import utils.color_print as cp
from agent import run_engineer_pipeline  
from conversion_pipeline import conversionWorkflow, ConversionWorkflowState
from summarizer_pipeline import summarizerWorkflow

load_dotenv()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class JsonRPCRequest(BaseModel):
    jsonrpc: str
    method: str
    params: Optional[dict] = {}
    id: Optional[Union[int, str]] = None

class ChatRequest(BaseModel):
    model: Optional[str] = "llama3.2"
    file_path: str
    message: str  # future prompt variations

async def fetch_github_repo_code(github_config: dict):
    cp.log_info('fetch_github_repo_code() called')
    headers = {
        "Authorization": f"token {github_config['token']}",
        "Accept": "application/vnd.github.v3+json"
    }
    async with httpx.AsyncClient(timeout=None, verify=False) as client:
        url = f"https://api.github.com/repos/{github_config['username']}/{github_config['repo']}/git/trees/main?recursive=1"
        response = await client.get(url, headers=headers)
        tree = response.json().get("tree", [])
        # cp.log_info("Received response from GitHub API for repo code", tree)
        documents = []
        for file in tree:
            if file["type"] == "blob" and file["path"].endswith((".py", ".js", ".jsx", ".html", ".java")):
                # cp.log_info(f"Fetching file: {file['path']}")
                raw_url = f"https://raw.githubusercontent.com/{github_config['username']}/{github_config['repo']}/main/{file['path']}"
                file_resp = await client.get(raw_url, headers=headers)
                documents.append({"name": file["path"], "content": file_resp.text})
        return documents

@app.post("/top-languages")
async def get_repo_top_languages(request: Request):
    cp.log_info('get_repo_top_languages() called')
    data = await request.json()
    github_config = data.get("github_config")
    headers = {
        "Authorization": f"token {github_config['token']}",
        "Accept": "application/vnd.github.v3+json"
    }
    async with httpx.AsyncClient(timeout=None, verify=False) as client:
        url = f"https://api.github.com/repos/{github_config['username']}/{github_config['repo']}/languages"
        response = await client.get(url, headers=headers)
        result = response.json()
        cp.log_info("Received response from GitHub API for languages", result)
        return {"result": result}

@app.post("/")
async def handle_rpc(request: Request):
    body = await request.json()
    try:
        rpc = JsonRPCRequest(**body) 
        if rpc.method == "get_context":
            cp.log_info('/get_context called')
            documents = await fetch_github_repo_code()
            return {"jsonrpc": "2.0", "id": rpc.id, "result": {"documents": documents}}

        elif rpc.method == "list_files":
            cp.log_info('/list_files called')
            documents = await fetch_github_repo_code()
            file_list = [doc["name"] for doc in documents]
            return {"jsonrpc": "2.0", "id": rpc.id, "result": {"files": file_list}}

        elif rpc.method == "run":
            cp.log_info('/run called')
            filename = rpc.params.get("filename")
            target_lang = rpc.params.get("target_language", "Python")

            documents = await fetch_github_repo_code()
            match = next((doc for doc in documents if doc["name"] == filename), None)
            if not match:
                return {"jsonrpc": "2.0", "id": rpc.id, "error": {"code": 404, "message": "File not found"}}

            return {"jsonrpc": "2.0", "id": rpc.id, "result": {
                "prompt": f"Translate the following code to {target_lang}:\n\n{match['content']}"
            }}

        else:
            return {"jsonrpc": "2.0", "id": rpc.id, "error": {"code": -32601, "message": "Method not found"}}
    except Exception as e:
        return {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": f"Parse error: {str(e)}"}}


@app.post("/chat")
async def chat_with_mcp(req: ChatRequest):
    try:
        result = await run_engineer_pipeline(file_name=req.file_path)
        return {"response": result}
    except Exception as e:
        return {"response": f"❌ Error /chat: {str(e)}"}

@app.post("/analyze")
async def analyze_file(request: Request):
    data = await request.json()
    filename = data.get("filename")
    github_config = data.get("github_config")
    model1_config = data.get("model1_config")

    if not github_config:
        return JSONResponse(status_code=400, content={"error": "Missing GitHub config"})

    docs = await fetch_github_repo_code(github_config)
    match = next((doc for doc in docs if doc["name"] == filename), None)
    if not match:
        cp.log_error(f"File {filename} not found in repository.")
        return JSONResponse(status_code=404, content={"error": "File not found"})

    cp.log_info("⚙️  engineer_task() called")
    state = ConversionWorkflowState(
        run_id = str(uuid4()),
        code=match["content"],
        file_path=filename,
        model1_config=model1_config
    )
    
    result = await conversionWorkflow.ainvoke(state)
    raw_output = result.get("json_spec", "")
    # cp.log_debug("🧠 Raw LLM Output:\n", raw_output)

    try:
        parsed = json.loads(raw_output) if (raw_output and isinstance(raw_output, str)) else raw_output
        cp.log_debug("🧠 Parsed LLM Output:\n", parsed)
    except Exception as e:
        cp.log_error(f"❌ Failed to parse LLM output: {e}")
        return {"error": str(e)}

    return {"result": raw_output}

@app.post("/analyze-all")
async def analyze_all_files(request: Request):
    data = await request.json()
    github_config = data.get("github_config")
    model1_config = data.get("model1_config")
    model2_config = data.get("model2_config")

    if not github_config:
        return JSONResponse(status_code=400, content={"error": "Missing GitHub config"})

    docs = await fetch_github_repo_code(github_config)
    results = []

    run_id = str(uuid4())
    for doc in docs:
        filename = doc["name"]
        content = doc["content"]

        cp.log_info(f"⚙️ Running engineer pipeline for: {filename}")
        conversion_state = ConversionWorkflowState(
            project_id="echo",
            run_id=run_id,
            code=content,
            file_path=filename,
            model1_config=model1_config,
            model2_config=model2_config
        )

        try:
            result = await conversionWorkflow.ainvoke(conversion_state)
            raw_output = result.get("json_spec", "")
            parsed = json.loads(raw_output)
            cp.log_debug(f"Parsed output keys for {filename}: {list(parsed.keys())}")

            results.append({"filename": filename, "result": parsed.get("output", parsed) })
        except Exception as e:
            cp.log_error(f"❌ Error analyzing {filename}: {e}")
            results.append({"filename": filename, "error": str(e)})

    # return {"results": results}

    cp.log_info("Running summarizer for all validated user stories...")

    summary_state = ConversionWorkflowState(
        project_id="delta",
        run_id=run_id,
        code="",
        model1_config=model1_config,
        model2_config=model2_config
    )
    summarizer_result = await summarizerWorkflow.ainvoke(summary_state)
    summary = summarizer_result.get("json_spec")

    return {"results": results, "summary": summary}

@app.post("/summarize")
async def summarize(request: Request):
    data = await request.json()
    run_id = data.get("run_id")
    model1_config = data.get("model1_config")

    if not run_id:
        return JSONResponse(status_code=400, content={"error": "Missing run_id"})

    summary_state = ConversionWorkflowState(
        project_id="delta",
        run_id=run_id,
        code="",
        model1_config=model1_config or {}
    )

    result = await summarizerWorkflow.ainvoke(summary_state)
    return {"summary": result.json_spec}


if __name__ == "__main__":
    cp.log_info("=========== Orion AI server ===========")