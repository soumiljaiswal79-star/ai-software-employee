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
    git_push,
    git_status,
)
from .github import (
    github_auth_status,
    github_create_branch,
    github_create_pull_request,
    github_get_branch,
    github_get_repository,
)


TOOL_DEFINITIONS = [
    {
        "name": "list_files",
        "description": "List files and directories inside workspace/.",
        "parameters": {
            "type": "object",
            "properties": {},
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
        },
    },
    {
        "name": "git_init",
        "description": "Initialize a Git repository inside workspace/.",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "git_status",
        "description": "Show the current Git working-tree status inside workspace/.",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "git_diff",
        "description": "Show the current unstaged Git diff inside workspace/.",
        "parameters": {
            "type": "object",
            "properties": {},
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
        },
    },
    {
        "name": "git_push",
        "description": (
            "Push a local Git branch to the configured origin remote. "
            "Only pushes the specified branch."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "branch_name": {
                    "type": "string",
                    "description": "Safe Git branch name to push.",
                }
            },
            "required": ["branch_name"],
        },
    },
    {
        "name": "github_auth_status",
        "description": (
            "Check whether the configured GitHub token is valid and return "
            "the authenticated GitHub username. Never expose the token."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "github_get_repository",
        "description": (
            "Check whether the authenticated GitHub account can access a "
            "specific repository and return basic repository information."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "owner": {
                    "type": "string",
                    "description": (
                        "GitHub repository owner username or organization."
                    ),
                },
                "repository": {
                    "type": "string",
                    "description": "GitHub repository name.",
                },
            },
            "required": ["owner", "repository"],
        },
    },
    {
        "name": "github_get_branch",
        "description": (
            "Check whether a GitHub branch exists and return its commit SHA."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "owner": {
                    "type": "string",
                    "description": (
                        "GitHub repository owner username or organization."
                    ),
                },
                "repository": {
                    "type": "string",
                    "description": "GitHub repository name.",
                },
                "branch": {
                    "type": "string",
                    "description": "GitHub branch name.",
                },
            },
            "required": ["owner", "repository", "branch"],
        },
    },
    {
        "name": "github_create_branch",
        "description": "Create a new GitHub branch from an existing branch.",
        "parameters": {
            "type": "object",
            "properties": {
                "owner": {
                    "type": "string",
                    "description": (
                        "GitHub repository owner username or organization."
                    ),
                },
                "repository": {
                    "type": "string",
                    "description": "GitHub repository name.",
                },
                "branch": {
                    "type": "string",
                    "description": "New GitHub branch name.",
                },
                "from_branch": {
                    "type": "string",
                    "description": (
                        "Existing GitHub branch to create the new branch from."
                    ),
                },
            },
            "required": ["owner", "repository", "branch"],
        },
    },
    {
        "name": "github_create_pull_request",
        "description": (
            "Create a GitHub pull request from a head branch into a base branch."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "owner": {
                    "type": "string",
                    "description": (
                        "GitHub repository owner username or organization."
                    ),
                },
                "repository": {
                    "type": "string",
                    "description": "GitHub repository name.",
                },
                "head": {
                    "type": "string",
                    "description": "Source branch containing the changes.",
                },
                "base": {
                    "type": "string",
                    "description": "Target branch that should receive the changes.",
                },
                "title": {
                    "type": "string",
                    "description": "Pull request title.",
                },
                "body": {
                    "type": "string",
                    "description": "Pull request description.",
                },
            },
            "required": [
                "owner",
                "repository",
                "head",
                "base",
                "title",
            ],
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
    "git_push": git_push,
    "github_auth_status": github_auth_status,
    "github_get_repository": github_get_repository,
    "github_get_branch": github_get_branch,
    "github_create_branch": github_create_branch,
    "github_create_pull_request": github_create_pull_request,
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


def execute_tool(
    name: str,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """Execute a registered tool with validated arguments."""
    handler = TOOL_HANDLERS.get(name)

    if handler is None:
        return {"error": f"Unknown tool: {name}"}

    try:
        return handler(**arguments)
    except TypeError:
        return {"error": f"Invalid arguments for tool: {name}"}