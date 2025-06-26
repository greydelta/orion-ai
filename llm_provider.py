from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_ollama import OllamaLLM

def build_llm(provider: str, model: str, api_key: str, temperature=0.5, top_p=1.0):
    if provider == "gemini":
        return ChatGoogleGenerativeAI(model=model, google_api_key=api_key, temperature=temperature, top_p=top_p)

    elif provider == "openrouter":
        return ChatOpenAI(model=model, api_key=api_key, openai_api_base="https://openrouter.ai/api/v1", temperature=temperature, top_p=top_p)

    elif provider == "ollama":
        return OllamaLLM(model=model, api_key=api_key, temperature=temperature, top_p=top_p)

    else:
        raise ValueError(f"Unsupported provider: {provider}")
