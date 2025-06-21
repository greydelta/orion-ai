import os, json

import httpx
import streamlit as st
from dotenv import load_dotenv

import utils.color_print as cp

load_dotenv()

LOCAL_MCP_SERVER_URL = os.getenv("LOCAL_MCP_SERVER_URL")
OLLAMA_URL = os.getenv("OLLAMA_URL")
try:
    OLLAMA_MODELS = json.loads(os.getenv("OLLAMA_MODELS"))
except json.JSONDecodeError:
    OLLAMA_MODELS = []

# Session State
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ^ --- Sidebar Settings ---
st.sidebar.title(":red[OrionAI]")

# & Milestone 1
st.sidebar.title(":blue[v1]")

model = st.sidebar.selectbox("Select Model", OLLAMA_MODELS)
github_file = st.sidebar.text_input("GitHub File Path", "src/App.java")
language = st.sidebar.text_input("Language", "Java")

# & Milestone 2
st.sidebar.title(":blue[v2]")

# GitHub Repository Selection
st.sidebar.subheader("Select GitHub Repository")
selected_repo_option = st.sidebar.selectbox(
    "Select GitHub Repo",
    ("repo1", "repo2"),
    index=None,
    placeholder="Select a repo...",
)
st.sidebar.write("Your selected repo: :orange[", selected_repo_option, "]")

# Junior and Senior Engineer Models
st.sidebar.subheader("Engineer Models")
junior_engineer_1_model = st.sidebar.selectbox("Select Junior Engineer 1 Model", OLLAMA_MODELS)
junior_engineer_2_model = st.sidebar.selectbox("Select Junior Engineer 2 Model", OLLAMA_MODELS)
senior_engineer_model = st.sidebar.selectbox("Select Senior Engineer Model", OLLAMA_MODELS)

# ^ --- Header ---
st.title("OrionAI: Code to Docs")
st.markdown("Select a model and GitHub repository to start analyzing. ")

# Chat Display
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat Input
user_input = st.chat_input("Type your message...")
if user_input:
    # Save user message
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Call MCP server
    try:
        response = httpx.post(
            f"{LOCAL_MCP_SERVER_URL}/chat",
            json={
                "model": model,
                "file_path": github_file,
                "message": user_input,
            },
            timeout=30.0
        )
        response.raise_for_status()
        reply = response.json().get("response", "⚠️ No response from MCP.")
    except Exception as e:
        reply = f"❌ Error: {e}"

    # Save assistant response
    st.session_state.chat_history.append({"role": "assistant", "content": reply})
    with st.chat_message("assistant"):
        st.markdown(reply)

if st.button("Analyze Code"):
    try:
        response = httpx.post(
            f"{LOCAL_MCP_SERVER_URL}/analyze",
            json={"filename": github_file},
            timeout=300
        )
        response.raise_for_status()
        raw = response.text
        cp.log_debug("📤 Raw LangGraph HTTP response:", raw)

        data = json.loads(raw)
        analysis = data.get("result", "No output")
        cp.log_debug("📤 Extracted analysis:", analysis)

    except Exception as e:
        analysis = f"❌ Error (app.py): {e}"

    with st.chat_message("assistant"):
        st.markdown("🧠 LangGraph Output")
        st.code(analysis, language="json")

if st.button("Get top language analysis"):
    try:
        response = httpx.post(
            f"{LOCAL_MCP_SERVER_URL}/top-languages",
            timeout=300
        )
        cp.log_debug("here:", response)
        response.raise_for_status()

        data = response.json()  # ✅ already a dict
        cp.log_debug("📤 Raw LangGraph HTTP response:", data)

        top = data.get("result", data)  # fallback to raw data if no .result
        cp.log_debug("📤 Top language analysis:", top)

    except Exception as e:
        top = f"❌ Error (app.py): {e}"

    with st.chat_message("assistant"):
        st.markdown("🧠 Top language analysis")
        st.code(top, language="json")
