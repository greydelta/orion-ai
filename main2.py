from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import your_mcp_client_module  # Replace this with your actual MCP logic import

app = FastAPI()

# CORS for Streamlit (optional if on same host)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    model: str
    file_path: str
    message: str

@app.post("/chat")
async def chat_with_mcp(req: ChatRequest):
    # Replace this with actual MCP call
    response = your_mcp_client_module.run_mcp_task(
        model=req.model,
        file_path=req.file_path,
        prompt=req.message
    )
    return {"response": response}
