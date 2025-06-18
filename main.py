from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import Optional, Union
import httpx
import os
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

GITHUB_TOKEN = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")

class JsonRPCRequest(BaseModel):
    jsonrpc: str
    method: str
    params: Optional[dict] = {}
    id: Optional[Union[int, str]] = None

async def fetch_github_repo_code():
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    async with httpx.AsyncClient(timeout=None, verify=False) as client:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/git/trees/main?recursive=1"
        response = await client.get(url, headers=headers)
        tree = response.json().get("tree", [])

        documents = []
        for file in tree:
            if file["type"] == "blob" and file["path"].endswith((".py", ".js", ".java")):
                raw_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{file['path']}"
                file_resp = await client.get(raw_url)
                documents.append({"name": file["path"], "content": file_resp.text})
        return documents

@app.post("/")
async def handle_rpc(request: Request):
    body = await request.json()
    try:
        rpc = JsonRPCRequest(**body)
        if rpc.method == "get_context":
            documents = await fetch_github_repo_code()
            return {"jsonrpc": "2.0", "id": rpc.id, "result": {"documents": documents}}

        elif rpc.method == "list_files":
            documents = await fetch_github_repo_code()
            file_list = [doc["name"] for doc in documents]
            return {"jsonrpc": "2.0", "id": rpc.id, "result": {"files": file_list}}

        elif rpc.method == "run":
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
