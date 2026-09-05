from __future__ import annotations

import os
import re
import subprocess
from typing import Any

from .filesystem import WORKSPACE_DIR


COMMAND_TIMEOUT_SECONDS = 10
MAX_OUTPUT_BYTES = 10_000

_BRANCH_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,99}$")


def _error(message: str) -> dict[str, Any]:
    return {
        "error": message,
        "stdout": "",
        "stderr": "",
        "exit_code": None,
    }


def _run_git(arguments: list[str]) -> dict[str, Any]:
    """Run one fixed Git operation inside workspace/."""
    try:
        process = subprocess.run(
            ["git", *arguments],
            cwd=WORKSPACE_DIR.resolve(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=COMMAND_TIMEOUT_SECONDS,
            env={
                "PATH": os.environ.get("PATH", ""),
                "GIT_TERMINAL_PROMPT": "0",
            },
        )
    except subprocess.TimeoutExpired:
        return _error("Git command timed out.")
    except OSError:
        return _error("Git is not available in the project environment.")

    stdout = process.stdout[:MAX_OUTPUT_BYTES]
    stderr = process.stderr[:MAX_OUTPUT_BYTES]

    result = {
        "stdout": stdout,
        "stderr": stderr,
        "exit_code": process.returncode,
    }

    if process.returncode != 0:
        result["error"] = stderr.strip() or "Git operation failed."

    return result


def git_init() -> dict[str, Any]:
    """Initialize a Git repository inside workspace/."""
    return _run_git(["init"])


def git_status() -> dict[str, Any]:
    """Return the current Git working-tree status."""
    return _run_git(["status", "--short"])


def git_diff() -> dict[str, Any]:
    """Return the current unstaged Git diff."""
    return _run_git(["diff", "--"])


def git_create_branch(branch_name: str) -> dict[str, Any]:
    """Create and switch to a safe branch name."""
    if not isinstance(branch_name, str) or not branch_name.strip():
        return _error("A branch name is required.")

    branch_name = branch_name.strip()

    if len(branch_name) > 100:
        return _error("Branch name is too long.")

    if not _BRANCH_NAME_PATTERN.fullmatch(branch_name):
        return _error("Invalid branch name.")

    if ".." in branch_name:
        return _error("Branch name cannot contain '..'.")

    if branch_name.startswith("-"):
        return _error("Branch name cannot start with '-'.")

    return _run_git(["switch", "-c", branch_name])


def git_commit(message: str) -> dict[str, Any]:
    """Create a Git commit using the supplied commit message."""
    if not isinstance(message, str) or not message.strip():
        return _error("A commit message is required.")

    message = message.strip()

    if len(message) > 200:
        return _error("Commit message is too long.")

    stage_result = _run_git(["add", "-A"])

    if stage_result.get("exit_code") != 0:
        return stage_result

    staged_result = _run_git(["diff", "--cached", "--quiet"])

    if staged_result.get("exit_code") == 0:
        return _error("There are no changes to commit.")

    if staged_result.get("exit_code") != 1:
        return staged_result

    return _run_git(["commit", "-m", message])
