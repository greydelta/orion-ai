import json

def parse_llm_response(raw_response) -> dict:
    """Safely parses LLM string response into a Python dict."""
    if isinstance(raw_response, dict):
        return raw_response
    if hasattr(raw_response, "content"):
        raw_response = raw_response.content
    try:
        return json.loads(raw_response)
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON from LLM: {e}", "raw": str(raw_response)}
