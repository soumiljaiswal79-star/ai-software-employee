import json
import os

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

from .tools.registry import GEMINI_TOOLS, execute_tool

load_dotenv()

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
MAX_TOOL_ROUNDS = 5

LLM_INSTRUCTIONS = (
    "You are an AI Software Employee working inside a controlled workspace. "
    "You can inspect and modify project files using the available filesystem tools. "
    "Use list_files only when you need to understand the project structure. "
    "Use read_file only when you actually need the contents of an existing file. "
    "If the user explicitly asks you to create a file and provides the exact "
    "content, use write_file directly without unnecessary list_files or read_file calls. "
    "If the user asks you to modify an existing file, read the file first unless "
    "the required complete content is already known. "
    "You can run safe tests with run_command. After modifying code, run an "
    "appropriate test when one is available. If a test fails, inspect the "
    "failure and attempt a correction. Never claim a test passed unless "
    "run_command returned a successful exit code. "
    "After completing the requested operation, give a concise response. "
    "Never claim that you inspected or modified a file unless you actually used "
    "the appropriate tool. "
    "Never access files outside workspace/."
)


class LLMConfigurationError(RuntimeError):
    """Raised when the LLM is not configured."""


class LLMAuthenticationError(RuntimeError):
    """Raised when Gemini rejects the configured credentials."""


class LLMRateLimitError(RuntimeError):
    """Raised when Gemini quota or rate limits are reached."""


class LLMServiceError(RuntimeError):
    """Raised when the LLM cannot return a response."""


def _raise_gemini_error(error: errors.APIError) -> None:
    if getattr(error, "code", None) in (401, 403):
        raise LLMAuthenticationError("Gemini authentication failed.") from error
    if getattr(error, "code", None) == 429:
        raise LLMRateLimitError("Gemini quota or rate limit exceeded.") from error
    raise LLMServiceError("The Gemini API could not process the request.") from error


def _generate_response(
    client: genai.Client, contents: list[types.Content]
) -> types.GenerateContentResponse:
    try:
        return client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=LLM_INSTRUCTIONS,
                tools=GEMINI_TOOLS,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(
                    disable=True
                ),
            ),
        )
    except errors.APIError as error:
        _raise_gemini_error(error)
    except Exception as error:
        raise LLMServiceError("The Gemini API could not process the request.") from error


def _function_calls(
    response: types.GenerateContentResponse,
) -> list[types.FunctionCall]:
    if not response.candidates or not response.candidates[0].content:
        return []

    return [
        part.function_call
        for part in response.candidates[0].content.parts or []
        if part.function_call is not None
    ]


def _run_tool(function_call: types.FunctionCall) -> dict[str, object]:
    name = function_call.name
    arguments = function_call.args

    if not isinstance(name, str) or not name:
        return {"error": "Malformed tool call."}
    if arguments is None:
        arguments = {}
    if not isinstance(arguments, dict):
        return {"error": "Malformed tool call."}

    return execute_tool(name, arguments)


def get_llm_response(message: str) -> tuple[str, list[str]]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise LLMConfigurationError(
            "GEMINI_API_KEY is not configured. Add it to the environment before using /chat."
        )

    client = genai.Client(api_key=api_key)
    contents = [
        types.Content(role="user", parts=[types.Part.from_text(text=message)])
    ]
    result = _generate_response(client, contents)
    tools_used: list[str] = []

    for _ in range(MAX_TOOL_ROUNDS):
        tool_calls = _function_calls(result)
        if not tool_calls:
            if not result.text:
                raise LLMServiceError("Gemini returned an empty response.")
            return result.text, tools_used

        if not result.candidates or not result.candidates[0].content:
            raise LLMServiceError("Gemini returned an invalid tool response.")
        contents.append(result.candidates[0].content)

        for tool_call in tool_calls:
            if tool_call.name and tool_call.name not in tools_used:
                tools_used.append(tool_call.name)
            contents.append(
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_function_response(
                            name=tool_call.name or "",
                            response={"result": _run_tool(tool_call)},
                        )
                    ],
                )
            )

        result = _generate_response(client, contents)

    raise LLMServiceError("The language model used too many tool-calling rounds.")
