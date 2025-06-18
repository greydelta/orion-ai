import httpx
import os
from dotenv import load_dotenv

load_dotenv()

LOCAL_MCP_SERVER_URL = os.getenv("LOCAL_MCP_SERVER_URL")
OLLAMA_URL = os.getenv("OLLAMA_URL")

async def list_files():
    payload = {
        "jsonrpc": "2.0",
        "method": "list_files",
        "params": {},
        "id": 2
    }
    async with httpx.AsyncClient(verify=False) as client:
        resp = await client.post(LOCAL_MCP_SERVER_URL, json=payload)
        return resp.json()["result"]["files"]

async def get_prompt_for_file(filename, target_language="Python"):
    payload = {
        "jsonrpc": "2.0",
        "method": "run",
        "params": {"filename": filename, "target_language": target_language},
        "id": 3
    }
    async with httpx.AsyncClient(timeout=None, verify=False) as client:
        resp = await client.post(LOCAL_MCP_SERVER_URL, json=payload)
        return resp.json()["result"]["prompt"]

async def get_context():
    payload = {
        "jsonrpc": "2.0",
        "method": "get_context",
        "params": {},
        "id": 1
    }
    async with httpx.AsyncClient(timeout=None, verify=False) as client:
        resp = await client.post(LOCAL_MCP_SERVER_URL, json=payload)
        # print("🔎 Full response from MCP tool:", resp.text)
        return resp.json()["result"]["documents"]

async def query_ollama(prompt):
    async with httpx.AsyncClient(timeout=None, verify=False) as client:
        resp = await client.post(f"{OLLAMA_URL}/api/generate", json={
            "model": "llama3.2",
            "prompt": prompt,
            "stream": False
        })
        print("🔎 Full response from Ollama: ", resp)
        return resp.json()["response"]

# async def run_agent():
#     docs = await get_context()
#     prompt = "Translate the following Java code to Python:\n\n" + docs[0]["content"]
#     response = await query_ollama(prompt)
#     print("\n🔁 Model Response:\n", response)

async def run_agent(file_name="Example.java", target_lang="Python"):
    docs = await get_context()

    # Find the specific file
    target_doc = next((doc for doc in docs if doc["name"] == file_name), None)
    if not target_doc:
        print(f"❌ File '{file_name}' not found.")
        return

    prompt = f"Translate the following Java code to {target_lang}:\n\n{target_doc['content']}"

    async with httpx.AsyncClient(timeout=None, verify=False) as client:
        resp = await client.post(f"{OLLAMA_URL}/api/generate", json={
            "model": "llama3.2",
            "prompt": prompt,
            "stream": False
        })
        response = resp.json()["response"]
        print(f"\n🔁 Model Response:\n\n{response}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_agent(file_name="src/App.java", target_lang="Python"))
