import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.tools.commands import MAX_OUTPUT_BYTES, run_command
from app.tools.filesystem import WORKSPACE_DIR


class RunCommandTests(unittest.TestCase):
    def test_allowed_python_command(self) -> None:
        result = run_command("python demo-project/hello.py")

        self.assertEqual(result["exit_code"], 0)
        self.assertEqual(result["stdout"].strip(), "Hello from the demo project!")
        self.assertFalse(result["timed_out"])

    def test_allowed_unittest_command(self) -> None:
        result = run_command("python -m unittest")

        self.assertEqual(result["exit_code"], 0)
        self.assertFalse(result["timed_out"])

    def test_pytest_command_is_allowlisted(self) -> None:
        result = run_command("python -m pytest")

        self.assertNotIn("error", result)
        self.assertIn(result["exit_code"], (0, 1, 2, 4, 5))
        self.assertFalse(result["timed_out"])

    def test_unsupported_command_is_rejected(self) -> None:
        result = run_command("rm -rf demo-project")

        self.assertIn("error", result)
        self.assertIsNone(result["exit_code"])

    def test_timeout_handling(self) -> None:
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".py",
            dir=WORKSPACE_DIR,
            delete=False,
            encoding="utf-8",
        ) as script:
            script.write("import time\ntime.sleep(1)\n")
            script_path = Path(script.name)

        try:
            relative_path = script_path.relative_to(WORKSPACE_DIR).as_posix()
            with patch("app.tools.commands.COMMAND_TIMEOUT_SECONDS", 0.1):
                result = run_command(f"python {relative_path}")
        finally:
            script_path.unlink(missing_ok=True)

        self.assertTrue(result["timed_out"])
        self.assertIsNone(result["exit_code"])

    def test_output_size_is_limited(self) -> None:
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".py",
            dir=WORKSPACE_DIR,
            delete=False,
            encoding="utf-8",
        ) as script:
            script.write(f"print('x' * {MAX_OUTPUT_BYTES * 3})\n")
            script_path = Path(script.name)

        try:
            relative_path = script_path.relative_to(WORKSPACE_DIR).as_posix()
            result = run_command(f"python {relative_path}")
        finally:
            script_path.unlink(missing_ok=True)

        self.assertEqual(result["exit_code"], 0)
        self.assertLessEqual(len(result["stdout"].encode("utf-8")), MAX_OUTPUT_BYTES)
        self.assertTrue(result["stdout_truncated"])

    def test_command_path_stays_inside_workspace(self) -> None:
        result = run_command("python ../app/main.py")

        self.assertIn("error", result)
        self.assertIn("Path traversal is not allowed.", result["error"])

    def test_sensitive_environment_is_not_passed_to_child(self) -> None:
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".py",
            dir=WORKSPACE_DIR,
            delete=False,
            encoding="utf-8",
        ) as script:
            script.write(
                "import os\n"
                "print('GEMINI_API_KEY' in os.environ)\n"
                "print('SESSION_SECRET' in os.environ)\n"
            )
            script_path = Path(script.name)

        try:
            relative_path = script_path.relative_to(WORKSPACE_DIR).as_posix()
            result = run_command(f"python {relative_path}")
        finally:
            script_path.unlink(missing_ok=True)

        self.assertEqual(result["exit_code"], 0)
        self.assertEqual(result["stdout"].splitlines(), ["False", "False"])


if __name__ == "__main__":
    unittest.main()