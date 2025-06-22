import json
from pathlib import Path
from typing import Optional

import utils.color_print as cp
from schemas.json_output_structures import get_engineer_example_json

class PromptLibrary:
    def __init__(self, base_path: str = "./prompts"):
        self.base_path = Path(base_path)

    def get_prompt_template(self, role: str) -> dict:
        """Load prompt JSON template for a specific agent role."""
        path = self.base_path / f"{role}.json"
        if not path.exists():
            raise FileNotFoundError(f"Prompt file for role '{role}' not found: {path}")
        return json.loads(path.read_text())

    def build_prompt(self, role: str, code: str) -> str:
        cp.log_info(f"Building prompt for role: {role}")
        """Render a complete prompt from the template, filling in the code and example JSON."""
        prompt = self.get_prompt_template(role)
        example_json = get_engineer_example_json() if role == "engineer" else "{}"
        formatted_prompt = f"""
{prompt['system']}

Instructions:
{prompt['instructions']}

Output Format:
{json.dumps(prompt['format'], indent=2)}

Rules:
- {'\n- '.join(prompt['rules'])}

Example Output:
{example_json}

Code:
{code}
        """
        cp.log_debug(f"📜 Prompt for role '{role}':\n{formatted_prompt}")
        return formatted_prompt

    def available_roles(self) -> list:
        """List all available roles in the prompt library."""
        return [f.stem for f in self.base_path.glob("*.json") if f.is_file()]
