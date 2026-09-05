from types import SimpleNamespace
import unittest
from unittest.mock import patch

from app.agent import MAX_AUTONOMOUS_ITERATIONS, TaskState, run_software_task
from app.main import ChatRequest, TaskRequest, chat, task


def function_response(name: str, arguments: dict[str, object]) -> SimpleNamespace:
    function_call = SimpleNamespace(name=name, args=arguments)
    part = SimpleNamespace(function_call=function_call)
    content = SimpleNamespace(parts=[part])
    return SimpleNamespace(
        text="",
        candidates=[SimpleNamespace(content=content)],
    )


def text_response(text: str) -> SimpleNamespace:
    return SimpleNamespace(text=text, candidates=[])


class FakeConversation:
    def __init__(self, responses: list[SimpleNamespace]) -> None:
        self.responses = iter(responses)
        self.user_messages: list[str] = []
        self.tool_results: list[dict[str, object]] = []

    def request(self) -> SimpleNamespace:
        return next(self.responses)

    def append_model_response(self, response: SimpleNamespace) -> None:
        return None

    def append_tool_result(
        self, function_call: SimpleNamespace, result: dict[str, object]
    ) -> None:
        self.tool_results.append({"name": function_call.name, "result": result})

    def append_user_message(self, message: str) -> None:
        self.user_messages.append(message)


class AutonomousAgentTests(unittest.TestCase):
    def test_successful_task_completion_and_file_modification(self) -> None:
        conversation = FakeConversation(
            [
                function_response("read_file", {"path": "demo-project/calculator.py"}),
                function_response(
                    "write_file",
                    {
                        "path": "demo-project/calculator.py",
                        "content": "def add(left, right):\n    return left + right\n",
                    },
                ),
                function_response(
                    "run_command",
                    {"command": "python demo-project/test_calculator.py"},
                ),
                text_response("The calculator was fixed and the test passed."),
            ]
        )

        def execute(name: str, arguments: dict[str, object]) -> dict[str, object]:
            if name == "read_file":
                return {"path": arguments["path"], "content": "return left - right"}
            if name == "write_file":
                return {"path": arguments["path"], "message": "File written successfully."}
            return {
                "command": arguments["command"],
                "stdout": "OK",
                "stderr": "",
                "exit_code": 0,
                "timed_out": False,
                "stdout_truncated": False,
                "stderr_truncated": False,
            }

        with patch("app.agent.execute_tool", side_effect=execute):
            state = run_software_task("Fix calculator", conversation=conversation)

        self.assertEqual(state.status, "completed")
        self.assertEqual(state.current_iteration, 1)
        self.assertEqual(state.files_modified, ["demo-project/calculator.py"])
        self.assertEqual(state.commands_run[0]["status"], "passed")
        self.assertEqual(
            [call["tool"] for call in state.tools_used],
            ["read_file", "write_file", "run_command"],
        )

    def test_failed_test_is_followed_by_correction_and_retest(self) -> None:
        conversation = FakeConversation(
            [
                function_response("read_file", {"path": "demo-project/calculator.py"}),
                function_response(
                    "write_file",
                    {"path": "demo-project/calculator.py", "content": "bad"},
                ),
                function_response(
                    "run_command",
                    {"command": "python demo-project/test_calculator.py"},
                ),
                text_response("The first test failed; I need to correct the code."),
                function_response(
                    "write_file",
                    {
                        "path": "demo-project/calculator.py",
                        "content": "def add(left, right):\n    return left + right\n",
                    },
                ),
                function_response(
                    "run_command",
                    {"command": "python demo-project/test_calculator.py"},
                ),
                text_response("The correction passed the test."),
            ]
        )
        run_count = 0

        def execute(name: str, arguments: dict[str, object]) -> dict[str, object]:
            nonlocal run_count
            if name == "write_file":
                return {"path": arguments["path"], "message": "File written successfully."}
            if name == "read_file":
                return {"path": arguments["path"], "content": "bad"}
            run_count += 1
            return {
                "command": arguments["command"],
                "stdout": "failed" if run_count == 1 else "OK",
                "stderr": "AssertionError" if run_count == 1 else "",
                "exit_code": 1 if run_count == 1 else 0,
                "timed_out": False,
                "stdout_truncated": False,
                "stderr_truncated": False,
            }

        with patch("app.agent.execute_tool", side_effect=execute):
            state = run_software_task("Fix calculator", conversation=conversation)

        self.assertEqual(state.status, "completed")
        self.assertEqual(state.current_iteration, 2)
        self.assertEqual(len(state.test_results), 2)
        self.assertEqual(state.test_results[0]["status"], "failed")
        self.assertEqual(state.test_results[1]["status"], "passed")
        self.assertEqual(len(conversation.user_messages), 1)

    def test_maximum_iteration_limit(self) -> None:
        conversation = FakeConversation(
            [text_response("The task is not verified.")] * MAX_AUTONOMOUS_ITERATIONS
        )

        state = run_software_task("Do not finish this task", conversation=conversation)

        self.assertEqual(state.status, "max_iterations_reached")
        self.assertEqual(state.current_iteration, MAX_AUTONOMOUS_ITERATIONS)
        self.assertEqual(len(conversation.user_messages), MAX_AUTONOMOUS_ITERATIONS - 1)

    def test_unsafe_command_and_workspace_restrictions_remain_blocked(self) -> None:
        from app.tools.registry import execute_tool

        unsupported = execute_tool("run_command", {"command": "env"})
        traversal = execute_tool(
            "run_command", {"command": "python ../app/main.py"}
        )

        self.assertIn("error", unsupported)
        self.assertIn("error", traversal)

    def test_existing_chat_endpoint_still_works(self) -> None:
        with patch(
            "app.main.get_llm_response",
            return_value=("mock response", ["list_files"]),
        ):
            response = chat(ChatRequest(message="inspect the project"))

        self.assertEqual(response, {"response": "mock response", "tools_used": ["list_files"]})

    def test_task_endpoint_returns_expected_structure(self) -> None:
        fake_state = TaskState(
            task="Fix calculator",
            current_iteration=2,
            files_modified=["demo-project/calculator.py"],
            commands_run=[{"command": "python demo-project/test_calculator.py"}],
            test_results=[{"status": "passed", "exit_code": 0}],
            status="completed",
            final_message="Verified.",
        )
        with patch("app.main.run_software_task", return_value=fake_state):
            response = task(TaskRequest(task="Fix calculator"))

        self.assertEqual(response["status"], "completed")
        self.assertEqual(response["iterations"], 2)
        self.assertEqual(response["response"], "Verified.")
        self.assertIn("files_read", response)
        self.assertIn("tools_used", response)