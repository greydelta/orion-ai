import json
from pathlib import Path
from typing import Optional

import utils.color_print as cp

class PromptLibrary:
    def __init__(self, base_path: str = "./prompts"):
        self.base_path = Path(base_path)

    def get_prompt_template(self, role: str, prompt_type: str = None) -> dict:
        """Load and optionally select a specific prompt template for a given role."""
        path = self.base_path / f"{role}.json"
        if not path.exists():
            raise FileNotFoundError(f"Prompt file for role '{role}' not found: {path}")
        
        templates = json.loads(path.read_text())

        if isinstance(templates, list):
            if prompt_type:
                for tpl in templates:
                    if tpl.get("type") == prompt_type:
                        return tpl
                raise ValueError(f"No prompt with type '{prompt_type}' found in {path}")
            else:
                return templates[0]  # default to first
        elif isinstance(templates, dict):
            return templates  # single template form
        else:
            raise ValueError(f"Invalid format in {path}")

    def build_prompt(self, role: str, prompt_type: str, code: str) -> tuple[str, str]:
        cp.log_info(f"Building prompt for role: {role}")
        """Render a complete prompt from the template, filling in the code and example JSON."""

        json_prompt = self.get_prompt_template(role, prompt_type)
        prompt_id = json_prompt.get("id", "unknown")

        system = json_prompt.get("system", "")
        instructions = json_prompt.get("instructions", "")
        rules = json_prompt.get("rules", [])
        example_json = json_prompt.get("format", {})

        formatted_prompt = f"""
            {system}

            Instructions:
            {instructions}

            Example Output Format:
            {json.dumps(example_json, indent=2)}

            Rules:
            - {'\n- '.join(rules)}

            Code:
            {code}
        """
        cp.log_debug(f"📜 Prompt for role '{role}':\n{formatted_prompt}")
        return formatted_prompt, prompt_id

    def get_role_details(self, role: str, prompt_type: str) -> tuple[str, str]:
        json_prompt = self.get_prompt_template(role, prompt_type)
        role = json_prompt.get("role", "unknown")
        role_id = json_prompt.get("role_id", "")
        cp.log_info(f"Retrieved role '{role}' with ID '{role_id}' for prompt type '{prompt_type}'")
        return role, role_id

    def available_roles(self) -> list:
        """List all available roles in the prompt library."""
        return [f.stem for f in self.base_path.glob("*.json") if f.is_file()]
