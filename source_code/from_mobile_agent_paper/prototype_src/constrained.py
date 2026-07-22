"""Constrained JSON decoding for VIntentAgent using llama.cpp built-in grammar.

Usage:
    from constrained import make_grammar, NULL_GRAMMAR

    # Grammar constraining tool to one of the retrieved tools (or null)
    grammar = make_grammar(["ACTION_SET_ALARM", "dial", "send_message"])

    response = model.create_chat_completion(
        messages=[...],
        grammar=grammar,
        temperature=0,
        max_tokens=256,
    )
"""
from __future__ import annotations

import json
from typing import Sequence


def build_response_schema(tool_names: Sequence[str]) -> dict:
    """Build a JSON schema for the tool-call response.

    The schema constrains:
    - tool  : one of the provided names or null
    - arguments : any JSON object
    - requires_confirmation : boolean (required)
    - status  : optional string ("clarification" | "unsupported")
    - message : optional string (clarification text)
    """
    tool_enum: list = sorted(set(tool_names))

    tool_type: dict
    if tool_enum:
        tool_type = {
            "anyOf": [
                {"type": "string", "enum": tool_enum},
                {"type": "null"},
            ]
        }
    else:
        tool_type = {"anyOf": [{"type": "string"}, {"type": "null"}]}

    return {
        "type": "object",
        "properties": {
            "tool": tool_type,
            "arguments": {"type": "object"},
            "requires_confirmation": {"type": "boolean"},
            "status": {
                "type": "string",
                "enum": ["clarification", "unsupported"],
            },
            "message": {"type": "string"},
        },
        "required": ["tool", "arguments", "requires_confirmation"],
        "additionalProperties": False,
    }


def make_grammar(tool_names: Sequence[str]):
    """Return a LlamaGrammar that constrains output to the response schema.

    Parameters
    ----------
    tool_names:
        Tool names that may appear in the ``tool`` field (retrieved candidates).
        Pass the full 24-tool list for the all-tools baseline.
    """
    from llama_cpp import LlamaGrammar  # lazy import — only needed at runtime

    schema = build_response_schema(tool_names)
    return LlamaGrammar.from_json_schema(json.dumps(schema))


# Pre-built grammar with no tool constraint (accepts any string or null).
# Used as a lightweight alternative when tool_names is unknown.
_UNCONSTRAINED_SCHEMA = {
    "type": "object",
    "properties": {
        "tool": {"anyOf": [{"type": "string"}, {"type": "null"}]},
        "arguments": {"type": "object"},
        "requires_confirmation": {"type": "boolean"},
        "status": {"type": "string", "enum": ["clarification", "unsupported"]},
        "message": {"type": "string"},
    },
    "required": ["tool", "arguments", "requires_confirmation"],
    "additionalProperties": False,
}


def make_unconstrained_grammar():
    """Grammar that only enforces JSON structure, not the tool enum."""
    from llama_cpp import LlamaGrammar

    return LlamaGrammar.from_json_schema(json.dumps(_UNCONSTRAINED_SCHEMA))
