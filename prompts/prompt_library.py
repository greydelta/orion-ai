import json
import yaml
import textwrap
from pathlib import Path
from typing import Optional, Union

import utils.color_print as cp

class PromptLibrary:
    def __init__(self, base_path: str = "./prompts"):
        self.base_path = Path(base_path)

    def get_prompt_template(self, role: str, prompt_type: str = None) -> dict:
        """Load and optionally select a specific prompt template for a given role."""
        cp.log_debug(f"Loading prompt template for role: {role}, type: {prompt_type}")

        folder = self.base_path / role
        yaml_path = folder / f"{prompt_type}.yaml"

        if yaml_path.exists():
            cp.log_debug(f"Reading YAML prompt: {yaml_path}")
            with open(yaml_path, 'r', encoding='utf-8') as f:
                templates = yaml.safe_load(f)
        else:
            raise FileNotFoundError(f"Prompt file for role '{role}' and type '{prompt_type}' not found in {folder}")

        if isinstance(templates, dict):
            return templates
        elif isinstance(templates, list):
            # This is rare in YAML unless you're batching multiple prompt templates
            for tpl in templates:
                if tpl.get("type") == prompt_type:
                    return tpl
            raise ValueError(f"No prompt with type '{prompt_type}' found in list")
        else:
            raise ValueError(f"Invalid YAML structure in {yaml_path}")

    def build_prompt(
            self, 
            role: str, 
            prompt_type: str, 
            code: Optional[str] = "", 
            json_output: Optional[Union[str, dict]] = None, 
            feedback: Optional[str] = "",
            json_list: Optional[Union[str, dict]] = None,
        ) -> tuple[str, str]:
        cp.log_info(f"Building prompt for role: {role}")

        prompt = self.get_prompt_template(role, prompt_type)
        prompt_id = prompt.get("id", "unknown")

        system = prompt.get("system", "")
        instructions = prompt.get("instructions", "")
        rules = prompt.get("rules", [])
        example_format = prompt.get("format", {}) 

        code_section = ""
        if code:
            code_section = f"""
            <code>
            {code}
            </code>
            """

        json_section = ""
        if json_output:
            try:
                if isinstance(json_output, dict):
                    json_str = json.dumps(json_output, indent=2, ensure_ascii=False)
                elif isinstance(json_output, str):
                    # json_str = json_output.encode("utf-8", errors="replace").decode("utf-8")
                    try:
                        parsed = json.loads(json_output)
                        json_str = json.dumps(parsed, indent=2, ensure_ascii=False)
                    except json.JSONDecodeError:
                        json_str = json_output
                else:
                    raise ValueError("json_output must be a dict or str")

                json_section = f"""
                <json>
                {json_str}
                </json>
                """
            except Exception as e:
                cp.log_error(f"⚠️ Error building json_section: {e}")
                json_section = "<json>[UNABLE TO SERIALIZE OUTPUT]</json>"
        
        if json_list:
            try:
                if isinstance(json_list, list):
                    json_str = json.dumps(json_list, indent=2, ensure_ascii=False)
                elif isinstance(json_list, str):
                    try:
                        parsed = json.loads(json_list)
                        json_str = json.dumps(parsed, indent=2, ensure_ascii=False)
                    except json.JSONDecodeError:
                        json_str = json_list
                else:
                    raise ValueError("json_list must be a list or JSON string")

                json_section = f"""
                <json_list>
                {json_str}
                </json_list>
                """
            except Exception as e:
                cp.log_error(f"⚠️ Error building json_list section: {e}")
                json_section = "<json_list>[UNABLE TO SERIALIZE LIST]</json_list>"

        feedback_section = ""
        if feedback:
            feedback_section = f"""
            <feedback>
            {feedback}
            </feedback>
            """

        formatted_prompt = f"""
            {system}

            <instructions>
            {instructions}
            </instructions>

            <rules>
            - {'\n- '.join(rules)}
            </rules>

            {code_section}

            {json_section}

            {feedback_section}

            <format>
            {example_format}
            </format>
        """.strip()

        cp.log_debug(f"📜 Prompt for role '{role}':\n{formatted_prompt}")
        return formatted_prompt, prompt_id

    def get_role_details(self, role: str, prompt_type: str) -> tuple[str, str]:
        prompt = self.get_prompt_template(role, prompt_type)

        role_obj = prompt.get("role", {})
        role_name = role_obj.get("name", "unknown")
        role_id = role_obj.get("id", "")
 
        cp.log_info(f"Retrieved role '{role_name}' with ID '{role_id}' for prompt type '{prompt_type}'")
        return role_name, role_id

    def available_roles(self) -> list:
        """List all available roles in the prompt library."""
        return [f.stem for f in self.base_path.glob("*.yaml") if f.is_file()]
