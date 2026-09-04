from typing import Any, Callable

from .filesystem import list_files, read_file


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
]


TOOL_HANDLERS: dict[str, Callable[..., dict[str, Any]]] = {
    "list_files": list_files,
    "read_file": read_file,
}


def execute_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    handler = TOOL_HANDLERS.get(name)
    if handler is None:
        return {"error": "Unknown tool."}

    try:
        return handler(**arguments)
    except TypeError:
        return {"error": "The tool arguments were invalid."}