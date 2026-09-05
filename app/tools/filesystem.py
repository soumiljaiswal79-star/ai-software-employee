import os
from pathlib import Path
from typing import Any


WORKSPACE_DIR = Path(__file__).resolve().parents[2] / "workspace"


def _ensure_workspace() -> Path:
    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
    return WORKSPACE_DIR


def _safe_path(path: str) -> Path:
    if not isinstance(path, str) or not path.strip():
        raise ValueError("A relative file path is required.")
    if "\x00" in path:
        raise ValueError("The file path is invalid.")

    requested_path = Path(path)
    if requested_path.is_absolute():
        raise ValueError("Absolute paths are not allowed.")
    if ".." in requested_path.parts:
        raise ValueError("Path traversal is not allowed.")

    workspace = _ensure_workspace().resolve()
    resolved_path = (workspace / requested_path).resolve(strict=False)

    try:
        resolved_path.relative_to(workspace)
    except ValueError as error:
        raise ValueError("The path must stay inside workspace/.") from error

    return resolved_path


def _relative_path(path: Path) -> str:
    return path.relative_to(_ensure_workspace().resolve()).as_posix()


def list_files() -> dict[str, list[str]]:
    """Return all non-symlink files and directories under workspace/."""
    workspace = _ensure_workspace()
    directories: list[str] = []
    files: list[str] = []

    for current_root, directory_names, file_names in os.walk(
        workspace, followlinks=False
    ):
        current_path = Path(current_root)
        directory_names[:] = sorted(
            name for name in directory_names if not (current_path / name).is_symlink()
        )
        file_names = sorted(
            name for name in file_names if not (current_path / name).is_symlink()
        )

        directories.extend(
            _relative_path(current_path / name) for name in directory_names
        )
        files.extend(_relative_path(current_path / name) for name in file_names)

    return {"directories": sorted(directories), "files": sorted(files)}


def read_file(path: str) -> dict[str, Any]:
    """Read a UTF-8 text file strictly inside workspace/."""
    try:
        safe_path = _safe_path(path)
    except ValueError as error:
        return {"error": str(error)}

    if not safe_path.exists():
        return {"error": f"File not found: {path}"}
    if not safe_path.is_file():
        return {"error": f"Path is not a file: {path}"}

    try:
        content = safe_path.read_bytes().decode("utf-8")
    except UnicodeDecodeError:
        return {"error": f"Binary files are not supported: {path}"}
    except OSError:
        return {"error": f"Unable to read file: {path}"}

    return {"path": _relative_path(safe_path), "content": content}


def write_file(path: str, content: str) -> dict[str, Any]:
    """Create or overwrite a UTF-8 text file strictly inside workspace/."""
    try:
        safe_path = _safe_path(path)
    except ValueError as error:
        return {"error": str(error)}

    if not isinstance(content, str):
        return {"error": "File content must be text."}

    # Prevent accidentally writing extremely large files.
    if len(content.encode("utf-8")) > 1_000_000:
        return {"error": "File content is too large. Maximum size is 1 MB."}

    try:
        safe_path.parent.mkdir(parents=True, exist_ok=True)
        safe_path.write_text(content, encoding="utf-8")
    except OSError:
        return {"error": f"Unable to write file: {path}"}

    return {
        "path": _relative_path(safe_path),
        "message": "File written successfully.",
    }
