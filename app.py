import os, json

import httpx
import streamlit as st
from dotenv import load_dotenv

import utils.color_print as cp
from streamlit_pages.logs_view import render_tab2

load_dotenv()

GITHUB_PERSONAL_ACCESS_TOKEN = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
API_KEY_GEMINI = os.getenv("API_KEY_GEMINI")
API_KEY_OPEN_ROUTER = os.getenv("API_KEY_OPEN_ROUTER")
LOCAL_MCP_SERVER_URL = os.getenv("LOCAL_MCP_SERVER_URL")
OLLAMA_URL = os.getenv("OLLAMA_URL")
try:
    OLLAMA_MODELS = json.loads(os.getenv("OLLAMA_MODELS"))
except json.JSONDecodeError:
    OLLAMA_MODELS = []

# ^ --- App Configs ---
st.set_page_config(layout="wide", page_title="OrionAI", page_icon="🚀")
    
st.title(":red[OrionAI]")
is_repo_analysis = False

tab1, tab2, tab3 = st.tabs(["🧠 Convert", "🗃️ Logs", "🔐 Env Vars"])

with tab1:

    # Session State
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # ^ --- Sidebar Settings ---
    st.sidebar.title(":violet[GitHub Configs]")
    gh_user = st.sidebar.text_input("User name", "greydelta")
    gh_token = st.sidebar.text_input("PAT", GITHUB_PERSONAL_ACCESS_TOKEN, type="password")

    st.sidebar.subheader(":blue[Single File Configs]")
    single_file = st.sidebar.text_input("File Path", "frontend/src/App.jsx")

    st.sidebar.subheader(":blue[Repo Configs]")
    gh_repo = st.sidebar.text_input("Repo name", "react-node-test")

    st.session_state["github_config"] = {
        "username": gh_user,
        "repo": gh_repo,
        "token": gh_token
    }
    github_config = st.session_state["github_config"]

    # ^ Agent Models
    st.sidebar.subheader("🔧 :blue[Agent Models]")

    sswe_model = st.sidebar.subheader("Select :blue[Senior Software Engineer / Product Manager] Model")
    with st.sidebar:

        provider1 = st.selectbox("Provider", ["gemini", "openrouter"], key="provider1")

        if provider1 == "openrouter":
            model_name = st.selectbox("Model", ["deepseek/deepseek-r1-0528:free"], key="provider1-1")
        elif provider1 == "gemini":
            model_name = st.selectbox("Model", ["gemini-2.5-flash"], key="provider1-2")

        api_key = st.text_input(f"{provider1.upper()} API Key", API_KEY_GEMINI, type="password", key="provider1-4")
        temperature = st.slider("Temperature", 0.0, 1.0, 0.2, key="provider1-5")
        top_p = st.slider("Top P", 0.0, 1.0, 1.0, key="provider1-6")

        st.session_state["model1_config"] = {
            "provider": provider1,
            "model_name": model_name,
            "api_key": api_key,
            "temperature": temperature,
            "top_p": top_p  
        }

    sssa_model = st.sidebar.subheader("Select :blue[Senior Software Solutions Architect] Model")
    with st.sidebar:

        provider2 = st.selectbox("Provider", ["gemini", "openrouter"], key="provider2")
        
        if provider2 == "openrouter":
            model_name = st.selectbox("Model", ["deepseek/deepseek-r1-0528:free"], key="provider2-1")
        elif provider2 == "gemini":
            model_name = st.selectbox("Model", ["gemini-2.5-flash"], key="provider2-2")

        api_key = st.text_input(f"{provider2.upper()} API Key", API_KEY_GEMINI, type="password", key="provider2-4")
        temperature = st.slider("Temperature", 0.0, 1.0, 0.5, key="provider2-5")
        top_p = st.slider("Top P", 0.0, 1.0, 1.0, key="provider2-6")

        st.session_state["model2_config"] = {
            "provider": provider2,
            "model_name": model_name,
            "api_key": api_key,
            "temperature": temperature,
            "top_p": top_p
        }

    # ^ --- Header ---
    st.subheader(":orange[Code to Docs]")
    st.markdown("Select an option and configure settings to start analyzing. ")

    # Chat Display
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat Input
    # user_input = st.chat_input("Type your message...")
    # if user_input:
    #     st.session_state.chat_history.append({"role": "user", "content": user_input})
    #     with st.chat_message("user"):
    #         st.markdown(user_input)

    #     try:
    #         response = httpx.post(
    #             f"{LOCAL_MCP_SERVER_URL}/chat",
    #             json={
    #                 "model": model,
    #                 "file_path": single_file,
    #                 "message": user_input,
    #             },
    #             timeout=30.0
    #         )
    #         response.raise_for_status()
    #         reply = response.json().get("response", "⚠️ No response from MCP.")
    #     except Exception as e:
    #         reply = f"❌ Error: {e}"

    #     st.session_state.chat_history.append({"role": "assistant", "content": reply})
    #     with st.chat_message("assistant"):
    #         st.markdown(reply)

    if st.button(f"Analyze :blue[{single_file}]"):
        github_config = st.session_state.get("github_config", {})
        model1_config = st.session_state.get("model1_config", {})

        try:
            response = httpx.post(
                f"{LOCAL_MCP_SERVER_URL}/analyze",
                json={"filename": single_file, "github_config": github_config, "model1_config": model1_config},
                timeout=500
            )
            response.raise_for_status()
            raw = response.text
            # cp.log_debug("📤 Raw LangGraph HTTP response:", raw)

            data = json.loads(raw)
            analysis = data.get("result", "No output")
            cp.log_debug("📤 Extracted analysis:", analysis)

        except Exception as e:
            analysis = f"❌ Error (app.py): {e}"

        with st.chat_message("assistant"):
            st.markdown("🧠 LangGraph Output")
            st.code(analysis, language="json")
    
    if st.button(f"Analyze Entire Repo :blue[{gh_user}/{gh_repo}]"):
        github_config = st.session_state.get("github_config", {})
        model1_config = st.session_state.get("model1_config", {})
        model2_config = st.session_state.get("model2_config", {})

        is_repo_analysis = True
        with st.spinner("Analyzing all files..."):
            try:
                response = httpx.post(
                    f"{LOCAL_MCP_SERVER_URL}/analyze-all",
                    json={"github_config": github_config, "model1_config": model1_config, "model2_config": model2_config},
                    timeout=2000
                )
                response.raise_for_status()
                raw = response.text
                # cp.log_debug("📤 Raw LangGraph HTTP response (all files):", raw)

                data = json.loads(raw)
                results = data.get("results", [])
                summary = data.get("summary", None)

                for res in results:
                    st.markdown(f"📁 `{res.get('filename')}`")
                    if "result" in res:
                        st.code(json.dumps(res["result"], indent=2), language="json")
                    else:
                        st.error(f"❌ Error: {res.get('error')}")
                
                if summary:
                    st.markdown("---")
                    st.subheader("📄 Summary of User Stories")
                    st.code(summary.strip(), language="markdown")

            except Exception as e:
                st.error(f"❌ Error triggering analysis: {e}")


    if st.button(f"Get top language for :blue[{gh_user}/{gh_repo}]"):
        github_config = st.session_state.get("github_config", {})

        try:
            response = httpx.post(
                f"{LOCAL_MCP_SERVER_URL}/top-languages",
                json={"github_config": github_config},
                timeout=300
            )
            cp.log_debug("here:", response)
            response.raise_for_status()

            data = response.json()
            # cp.log_debug("📤 Raw LangGraph HTTP response:", data)

            top = data.get("result", data)
            cp.log_debug("📤 Top language analysis:", top)

        except Exception as e:
            top = f"❌ Error (app.py): {e}"

        with st.chat_message("assistant"):
            st.markdown("🧠 Top language analysis")
            st.code(top, language="json")

    st.subheader("Summarize User Stories")

    run_id = st.text_input("Enter `run_id` to summarize")

    if st.button("🧠 Summarize"):
        model1_config = st.session_state.get("model1_config", {})
        model2_config = st.session_state.get("model2_config", {})
        if not run_id:
            st.warning("⚠️ Please enter a valid `run_id` to summarize.")
        else:
            model2_config = st.session_state.get("model2_config", {})

            try:
                response = httpx.post(
                    f"{LOCAL_MCP_SERVER_URL}/summarize",
                    json={
                        "run_id": run_id,
                        "model1_config": model1_config
                    },
                    timeout=300
                )
                response.raise_for_status()
                summary_result = json.loads(response.text)
                summary = summary_result.get("summary", "No summary returned")

                with st.chat_message("assistant"):
                    st.markdown("📝 **User Story Summary:**")
                    st.code(summary, language="json")

            except Exception as e:
                st.error(f"❌ Error calling summarizer: {e}")

with tab2:
    render_tab2(is_repo_analysis)


with tab3:
    # print app environment variables
    st.subheader(":blue[Env variables]")
    CUSTOM_ENV_KEYS = ["OLLAMA_URL", "OLLAMA_MODELS", "LOCAL_MCP_SERVER_URL", "GITHUB_REPO", "GITHUB_PERSONAL_ACCESS_TOKEN", "SUPABASE_DB_URL"]

    filtered_env = {k: os.getenv(k) for k in CUSTOM_ENV_KEYS}
    st.code(json.dumps(filtered_env, indent=2), language="json")