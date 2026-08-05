from __future__ import annotations

from typing import Any

from common import load_json, TOOLS_PATH


def _type_matches(value: Any, expected: str) -> bool:
    checks = {
        "string": lambda item: isinstance(item, str),
        "integer": lambda item: isinstance(item, int) and not isinstance(item, bool),
        "boolean": lambda item: isinstance(item, bool),
        "array": lambda item: isinstance(item, list),
        "object": lambda item: isinstance(item, dict),
    }
    return expected in checks and checks[expected](value)


class ToolValidator:
    def __init__(self, tools_path=TOOLS_PATH):
        self.tools = {tool["name"]: tool for tool in load_json(tools_path)}

    def validate(self, prediction: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        tool_name = prediction.get("tool")
        status = prediction.get("status")

        if tool_name is None:
            if status not in {"clarification", "unsupported", "rejected"}:
                errors.append("null tool requires clarification, unsupported or rejected status")
            return errors

        tool = self.tools.get(tool_name)
        if tool is None:
            return [f"unknown tool: {tool_name}"]

        arguments = prediction.get("arguments")
        if not isinstance(arguments, dict):
            return ["arguments must be an object"]

        schema = tool.get("arguments", {})
        unknown = sorted(set(arguments) - set(schema))
        if unknown:
            errors.append(f"unknown arguments: {', '.join(unknown)}")

        for name, argument_schema in schema.items():
            required = argument_schema.get("required", False)
            if required and (name not in arguments or arguments[name] is None):
                errors.append(f"missing required argument: {name}")
                continue
            if name not in arguments or arguments[name] is None:
                continue

            value = arguments[name]
            expected_type = argument_schema.get("type")
            if not _type_matches(value, expected_type):
                errors.append(f"{name} must be {expected_type}")
                continue

            if "enum" in argument_schema and value not in argument_schema["enum"]:
                errors.append(f"{name} is outside enum")
            if expected_type == "integer":
                if "minimum" in argument_schema and value < argument_schema["minimum"]:
                    errors.append(f"{name} is below minimum")
                if "maximum" in argument_schema and value > argument_schema["maximum"]:
                    errors.append(f"{name} is above maximum")
            if expected_type == "array" and "items" in argument_schema:
                item_type = argument_schema["items"]
                if any(not _type_matches(item, item_type) for item in value):
                    errors.append(f"{name} contains invalid item type")

        expected_confirmation = bool(tool.get("confirmation"))
        if prediction.get("requires_confirmation") != expected_confirmation:
            errors.append(
                f"requires_confirmation must be {str(expected_confirmation).lower()}"
            )
        return errors

