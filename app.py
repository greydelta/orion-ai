# import streamlit as st
# import pandas as pd

# st.write("Hello world")
# st.write("Here's our first attempt at using data to create a table:")
# st.write(pd.DataFrame({
#     'first column': [1, 2, 3, 4],
#     'second column': [10, 20, 30, 40]
# }))

import streamlit as st
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

LOCAL_MCP_SERVER_URL = os.getenv("LOCAL_MCP_SERVER_URL")
OLLAMA_URL = os.getenv("OLLAMA_URL")

# --- Configuration ---
OLLAMA_MODELS = ["llama3.2", "codellama"]  # Extend as needed

# --- Session State ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- Sidebar Settings ---
st.sidebar.title("Settings")
model = st.sidebar.selectbox("Select Ollama Model", OLLAMA_MODELS)
github_file = st.sidebar.text_input("GitHub File Path", "src/main.java")

# --- Header ---
st.title("💬 Code Translator Chat (MCP + Ollama)")
st.markdown("Talk to your MCP-backed code translator. Select a model and file, then start chatting.")

# --- Chat Display ---
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Chat Input ---
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

