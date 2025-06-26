import json
import re
from typing import Optional, Type
from pydantic import BaseModel, ValidationError

def extract_json(text: str | dict) -> Optional[str]:
    if isinstance(text, dict):
        return text
    match = re.search(r"\{.*\}", text, re.DOTALL)
    return match.group(0) if match else None

def validate_llm_output(
    raw_output: str | dict,
    schema_model: Type[BaseModel]
) -> tuple[Optional[BaseModel], Optional[str]]:
    try:
        if isinstance(raw_output, dict):
            parsed = raw_output
        else:
            json_text = extract_json(raw_output)
            if not json_text:
                return None, "No JSON object found"
            parsed = json.loads(json_text)

        validated = schema_model(**parsed)
        return validated, None

    except (json.JSONDecodeError, ValidationError, TypeError) as e:
        return None, str(e)
