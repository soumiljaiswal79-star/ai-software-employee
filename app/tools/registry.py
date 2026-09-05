from __future__ import annotations

from typing import Any

from google.genai import types

from .filesystem import list_files, read_file, write_file
from .commands import run_command
from .git import (
    git_commit,
    git_create_branch,
    git_diff,
    git_init,
    git_status,
)


TOOL_DEFINITIONS = [
    {
        "name": "list_files",
        "description": "List files and directories inside workspace/.",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "name": "read_file",
        "description": "Read a UTF-8 text file inside workspace/.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Workspace-relative file path.",
                }
            },
            "required": ["path"],
            "additionalProperties": False,
        },
    },
    {
        "name": "write_file",
        "description": "Create or overwrite a UTF-8 text file inside workspace/.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Workspace-relative file path.",
                },
                "content": {
                    "type": "string",
                    "description": "Complete text content to write.",
                },
            },
            "required": ["path", "content"],
            "additionalProperties": False,
        },
    },
    {
        "name": "run_command",
        "description": (
            "Run a safe allowlisted Python command inside workspace/. "
            "Supported commands are Python workspace scripts, pytest, and unittest."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": (
                        "Allowed command such as "
                        "'python demo-project/test.py', "
                        "'python -m pytest', or "
                        "'python -m unittest'."
                    ),
                }
            },
            "required": ["command"],
            "additionalProperties": False,
        },
    },
    {
        "name": "git_init",
        "description": "Initialize a Git repository inside workspace/.",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "name": "git_status",
        "description": "Show the current Git working-tree status inside workspace/.",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "name": "git_diff",
        "description": "Show the current unstaged Git diff inside workspace/.",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "name": "git_create_branch",
        "description": "Create and switch to a new Git branch inside workspace/.",
        "parameters": {
            "type": "object",
            "properties": {
                "branch_name": {
                    "type": "string",
                    "description": "Safe Git branch name.",
                }
            },
            "required": ["branch_name"],
            "additionalProperties": False,
        },
    },
    {
        "name": "git_commit",
        "description": "Stage all workspace changes and create a Git commit.",
        "parameters": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Git commit message.",
                }
            },
            "required": ["message"],
            "additionalProperties": False,
        },
    },
]


TOOL_HANDLERS = {
    "list_files": list_files,
    "read_file": read_file,
    "write_file": write_file,
    "run_command": run_command,
    "git_init": git_init,
    "git_status": git_status,
    "git_diff": git_diff,
    "git_create_branch": git_create_branch,
    "git_commit": git_commit,
}


GEMINI_TOOLS = [
    types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name=tool["name"],
                description=tool["description"],
                parameters=tool["parameters"],
            )
        ]
    )
    for tool in TOOL_DEFINITIONS
]


def execute_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Execute a registered tool with validated arguments."""
    handler = TOOL_HANDLERS.get(name)

    if handler is None:
        return {"error": f"Unknown tool: {name}"}

    try:
        return handler(**arguments)
    except TypeError:
        return {"error": f"Invalid arguments for tool: {name}"}
