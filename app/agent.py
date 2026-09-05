from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any

from google.genai import types

from .llm import (
    GeminiConversation,
    LLMServiceError,
    _function_calls,
)
from .tools.registry import execute_tool


MAX_AUTONOMOUS_ITERATIONS = 5
MAX_TOOL_ROUNDS_PER_ITERATION = 10

AUTONOMOUS_INSTRUCTIONS = (
    "You are an autonomous software developer working only inside workspace/. "
    "Complete the user's task through a controlled loop: understand, inspect, "
    "modify, test, analyze actual output, fix failures, retest, and report. "
    "Inspect relevant files before changing existing code and make the smallest "
    "reasonable change. After modifying code, use run_command for an appropriate "
    "test. If the test fails, inspect its actual stdout and stderr, correct the "
    "code, and run the test again. Never claim success without a successful "
    "run_command result. Do not access anything outside workspace/, do not "
    "attempt unsupported commands, do not access secrets, and do not modify "
    "security mechanisms or application configuration. Stop once the task is "
    "verified or when the iteration limit is reached."
)

_SECRET_LIKE_TEXT = re.compile(
    r"(?i)(gemini_api_key|session_secret|api[_-]?key|secret)"
    r"(\s*[:=]\s*)[^\s,;]+"
)
_TOKEN_LIKE_TEXT = re.compile(r"\bAIza[0-9A-Za-z_-]{20,}\b")


@dataclass
class TaskState:
    task: str
    current_iteration: int = 0
    maximum_iterations: int = MAX_AUTONOMOUS_ITERATIONS
    tools_used: list[dict[str, Any]] = field(default_factory=list)
    files_read: list[str] = field(default_factory=list)
    files_modified: list[str] = field(default_factory=list)
    commands_run: list[dict[str, Any]] = field(default_factory=list)
    test_results: list[dict[str, Any]] = field(default_factory=list)
    status: str = "running"
    final_message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _redact_text(value: str) -> str:
    value = _SECRET_LIKE_TEXT.sub(r"\1\2[REDACTED]", value)
    return _TOKEN_LIKE_TEXT.sub("[REDACTED]", value)


def _unique_append(values: list[str], value: Any) -> None:
    if isinstance(value, str) and value and value not in values:
        values.append(value)


def _safe_arguments(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if name == "write_file":
        return {
            "path": arguments.get("path"),
            "content_length": (
                len(arguments["content"])
                if isinstance(arguments.get("content"), str)
                else None
            ),
        }
    if name == "run_command":
        command = arguments.get("command")
        return {"command": _redact_text(command) if isinstance(command, str) else None}
    if name == "read_file":
        return {"path": arguments.get("path")}
    return {}


def _action_for_tool(name: str) -> str:
    if name in {"list_files", "read_file"}:
        return "inspection"
    if name == "write_file":
        return "modification"
    if name == "run_command":
        return "test_execution"
    return "other"


def _run_status(name: str, result: dict[str, Any]) -> str:
    if "error" in result:
        return "error"
    if name != "run_command":
        return "success"
    if result.get("timed_out"):
        return "timed_out"
    if result.get("exit_code") == 0:
        return "passed"
    return "failed"


def _record_tool_call(
    state: TaskState,
    name: str,
    arguments: dict[str, Any],
    result: dict[str, Any],
    iteration: int,
) -> None:
    result_status = _run_status(name, result)
    state.tools_used.append(
        {
            "tool": name,
            "action": _action_for_tool(name),
            "arguments": _safe_arguments(name, arguments),
            "result_status": result_status,
            "iteration": iteration,
        }
    )

    if name == "read_file" and result_status == "success":
        _unique_append(state.files_read, result.get("path"))
    elif name == "write_file" and result_status == "success":
        _unique_append(state.files_modified, result.get("path"))
    elif name == "run_command":
        command = arguments.get("command", "")
        command = _redact_text(command) if isinstance(command, str) else ""
        command_record = {
            "command": command,
            "status": result_status,
            "exit_code": result.get("exit_code"),
            "timed_out": bool(result.get("timed_out")),
            "iteration": iteration,
        }
        state.commands_run.append(command_record)
        state.test_results.append(
            {
                **command_record,
                "stdout": _redact_text(str(result.get("stdout", ""))),
                "stderr": _redact_text(str(result.get("stderr", ""))),
            }
        )


def _has_verified_test(state: TaskState) -> bool:
    return any(
        result["status"] == "passed"
        and result["exit_code"] == 0
        and not result["timed_out"]
        for result in state.test_results
    )


def _execute_tracked_tool(
    state: TaskState,
    function_call: types.FunctionCall,
    iteration: int,
) -> dict[str, Any]:
    name = function_call.name
    arguments = function_call.args

    if not isinstance(name, str) or not name:
        result = {"error": "Malformed tool call."}
        _record_tool_call(state, "", {}, result, iteration)
        return result
    if arguments is None:
        arguments = {}
    if not isinstance(arguments, dict):
        result = {"error": "Malformed tool call."}
        _record_tool_call(state, name, {}, result, iteration)
        return result

    result = execute_tool(name, arguments)
    _record_tool_call(state, name, arguments, result, iteration)
    return result


def _continuation_prompt(iteration: int) -> str:
    return (
        f"Continue the same software task in autonomous iteration {iteration} "
        f"of {MAX_AUTONOMOUS_ITERATIONS}. Use the existing tool results as the "
        "source of truth. If the last test failed, inspect the failure and fix "
        "the smallest relevant file, then rerun the test. If it passed, stop "
        "and provide a concise evidence-based report."
    )


def run_software_task(
    task: str,
    *,
    conversation: GeminiConversation | None = None,
) -> TaskState:
    """Run one bounded autonomous software task and return its execution state."""
    if not isinstance(task, str) or not task.strip():
        raise ValueError("A software task is required.")

    state = TaskState(task=task)
    conversation = conversation or GeminiConversation(
        task,
        system_instruction=AUTONOMOUS_INSTRUCTIONS,
    )

    for iteration in range(1, MAX_AUTONOMOUS_ITERATIONS + 1):
        state.current_iteration = iteration
        if iteration > 1:
            conversation.append_user_message(_continuation_prompt(iteration))

        final_text = ""
        for _ in range(MAX_TOOL_ROUNDS_PER_ITERATION):
            response = conversation.request()
            tool_calls = _function_calls(response)
            if not tool_calls:
                final_text = response.text or ""
                break

            conversation.append_model_response(response)
            for tool_call in tool_calls:
                result = _execute_tracked_tool(state, tool_call, iteration)
                conversation.append_tool_result(tool_call, result)

        if final_text:
            state.final_message = _redact_text(final_text)

        if _has_verified_test(state):
            state.status = "completed"
            if not state.final_message:
                state.final_message = (
                    "The task was completed and verified by a successful test command."
                )
            return state

    state.status = "max_iterations_reached"
    if not state.final_message:
        state.final_message = (
            "The task was not verified successfully within the maximum number "
            "of autonomous iterations."
        )
    else:
        state.final_message = (
            f"{state.final_message}\n\n"
            "The task was not verified successfully within the maximum number "
            "of autonomous iterations."
        )
    return state