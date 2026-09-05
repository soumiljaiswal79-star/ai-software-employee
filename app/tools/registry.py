from typing import Any, Callable

from google.genai import types

from .commands import run_command
from .filesystem import list_files, read_file, write_file


TOOL_DEFINITIONS = [
    {
        "type": "function",
        "name": "list_files",
        "description": (
            "Recursively list files and directories inside workspace/. "
            "Use this when you need to inspect the available project structure."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "read_file",
        "description": (
            "Read a UTF-8 text file inside workspace/ using a relative path. "
            "Use this when you need the contents of a specific project file. "
            "Absolute paths, path traversal, and binary files are rejected."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": (
                        "Relative path inside workspace/, such as "
                        "demo-project/README.md."
                    ),
                }
            },
            "required": ["path"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "write_file",
        "description": (
            "Create or overwrite a UTF-8 text file inside workspace/. "
            "Use this when you need to create or modify a project file. "
            "The path must be relative and stay inside workspace/."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": (
                        "Relative path inside workspace/, such as demo-project/app.py."
                    ),
                },
                "content": {
                    "type": "string",
                    "description": "The complete UTF-8 text content to write.",
                },
            },
            "required": ["path", "content"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "run_command",
        "description": (
            "Run one safe Python command from workspace/. Supported commands are "
            "python <relative .py file>, python -m pytest, and python -m unittest. "
            "Commands have a timeout and bounded output; shell commands are rejected."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": (
                        "One supported command, such as "
                        "'python demo-project/hello.py' or 'python -m unittest'."
                    ),
                }
            },
            "required": ["command"],
            "additionalProperties": False,
        },
    },
]


TOOL_HANDLERS: dict[str, Callable[..., dict[str, Any]]] = {
    "list_files": list_files,
    "read_file": read_file,
    "write_file": write_file,
    "run_command": run_command,
}


GEMINI_TOOLS = [
    types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name=definition["name"],
                description=definition["description"],
                parameters_json_schema=definition["parameters"],
            )
            for definition in TOOL_DEFINITIONS
        ]
    )
]


def execute_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    handler = TOOL_HANDLERS.get(name)
    if handler is None:
        return {"error": "Unknown tool."}

    try:
        return handler(**arguments)
    except TypeError:
        return {"error": "The tool arguments were invalid."}
