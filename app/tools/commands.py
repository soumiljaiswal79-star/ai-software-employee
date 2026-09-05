import os
import shlex
import signal
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any

from .filesystem import WORKSPACE_DIR, _safe_path


COMMAND_TIMEOUT_SECONDS = 5.0
MAX_OUTPUT_BYTES = 10_000
_READ_CHUNK_BYTES = 4_096


def _error(message: str) -> dict[str, Any]:
    return {
        "error": message,
        "stdout": "",
        "stderr": "",
        "exit_code": None,
        "timed_out": False,
        "stdout_truncated": False,
        "stderr_truncated": False,
    }


def _python_executable() -> str:
    """Return the Python executable associated with the project environment."""
    project_python = Path(".pythonlibs/bin/python").resolve()

    if project_python.is_file() and os.access(project_python, os.X_OK):
        return str(project_python)

    return sys.executable


def _parse_command(command: str) -> tuple[list[str] | None, str | None]:
    if not isinstance(command, str) or not command.strip():
        return None, "A command is required."

    if "\x00" in command:
        return None, "The command is invalid."

    try:
        tokens = shlex.split(command)
    except ValueError:
        return None, "The command syntax is invalid."

    if len(tokens) == 2 and tokens[0] == "python":
        script_path = tokens[1]

        if script_path.startswith("-"):
            return None, "Only a Python script path is allowed."

        if not script_path.endswith(".py"):
            return None, "Only Python files can be executed."

        try:
            safe_path = _safe_path(script_path)
        except ValueError as error:
            return None, str(error)

        if not safe_path.exists():
            return None, f"File not found: {script_path}"

        if not safe_path.is_file():
            return None, f"Path is not a file: {script_path}"

        relative_path = safe_path.relative_to(
            WORKSPACE_DIR.resolve()
        ).as_posix()

        return [_python_executable(), relative_path], None

    if tokens == ["python", "-m", "pytest"]:
        return [_python_executable(), "-m", "pytest"], None

    if tokens == ["python", "-m", "unittest"]:
        return [_python_executable(), "-m", "unittest"], None

    return (
        None,
        "Command not allowed. Supported commands are: "
        "python <workspace-relative .py file>, "
        "python -m pytest, "
        "and python -m unittest.",
    )


def _read_limited(stream: Any) -> tuple[str, bool]:
    chunks: list[bytes] = []
    total_bytes = 0
    truncated = False

    while True:
        chunk = stream.read(_READ_CHUNK_BYTES)

        if not chunk:
            break

        total_bytes += len(chunk)

        if total_bytes <= MAX_OUTPUT_BYTES:
            chunks.append(chunk)
        elif not truncated:
            allowed = MAX_OUTPUT_BYTES - (
                total_bytes - len(chunk)
            )

            if allowed > 0:
                chunks.append(chunk[:allowed])

            truncated = True

    return (
        b"".join(chunks).decode("utf-8", errors="replace"),
        truncated,
    )


def _safe_environment() -> dict[str, str]:
    """Provide only non-sensitive runtime values to the child process."""
    environment: dict[str, str] = {
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUNBUFFERED": "1",
    }

    path = os.environ.get("PATH")

    if path:
        environment["PATH"] = path

    return environment


def _terminate_process(process: subprocess.Popen[Any]) -> None:
    """Terminate a timed-out process in a platform-safe way."""
    if os.name == "nt":
        try:
            process.kill()
        except ProcessLookupError:
            pass
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def run_command(command: str) -> dict[str, Any]:
    """Run one allowlisted Python command from the workspace directory."""
    argv, parse_error = _parse_command(command)

    if parse_error:
        return _error(parse_error)

    workspace = WORKSPACE_DIR.resolve()

    try:
        process = subprocess.Popen(
            argv or [],
            cwd=workspace,
            env=_safe_environment(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
    except OSError:
        return _error("The allowed command could not be started.")

    assert process.stdout is not None
    assert process.stderr is not None

    stdout_result: list[tuple[str, bool]] = []
    stderr_result: list[tuple[str, bool]] = []

    stdout_thread = threading.Thread(
        target=lambda: stdout_result.append(
            _read_limited(process.stdout)
        ),
        daemon=True,
    )

    stderr_thread = threading.Thread(
        target=lambda: stderr_result.append(
            _read_limited(process.stderr)
        ),
        daemon=True,
    )

    stdout_thread.start()
    stderr_thread.start()

    timed_out = False

    try:
        process.wait(timeout=COMMAND_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        timed_out = True

        _terminate_process(process)

        process.wait()

    stdout_thread.join()
    stderr_thread.join()

    stdout, stdout_truncated = stdout_result[0]
    stderr, stderr_truncated = stderr_result[0]

    process.stdout.close()
    process.stderr.close()

    return {
        "command": command,
        "stdout": stdout,
        "stderr": stderr,
        "exit_code": None if timed_out else process.returncode,
        "timed_out": timed_out,
        "stdout_truncated": stdout_truncated,
        "stderr_truncated": stderr_truncated,
    }