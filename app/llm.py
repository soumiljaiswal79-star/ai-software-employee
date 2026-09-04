import json
import os

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError

from .tools.registry import TOOL_DEFINITIONS, execute_tool

load_dotenv()

LLM_INSTRUCTIONS = (
    "You are an AI Software Employee. You may inspect project files only through "
    "the provided filesystem tools, which are limited to workspace/. When a user "
    "asks about files or project contents, use the relevant tool before answering. "
    "Never access or describe arbitrary server paths."
)


class LLMConfigurationError(RuntimeError):
    """Raised when the LLM is not configured."""


class LLMServiceError(RuntimeError):
    """Raised when the LLM cannot return a response."""


def get_llm_response(message: str) -> tuple[str, list[str]]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise LLMConfigurationError(
            "OPENAI_API_KEY is not configured. Add it to the environment before using /chat."
        )

    client = OpenAI(api_key=api_key)

    try:
        result = client.responses.create(
            model="gpt-4o-mini",
            input=message,
            instructions=LLM_INSTRUCTIONS,
            tools=TOOL_DEFINITIONS,
        )
    except OpenAIError as error:
        raise LLMServiceError("The language model could not process the request.") from error

    tools_used: list[str] = []

    for _ in range(5):
        tool_calls = [
            item
            for item in result.output
            if getattr(item, "type", None) == "function_call"
        ]

        if not tool_calls:
            return result.output_text, tools_used

        tool_outputs = []
        for tool_call in tool_calls:
            tool_name = tool_call.name
            if tool_name not in tools_used:
                tools_used.append(tool_name)

            try:
                arguments = json.loads(tool_call.arguments or "{}")
                if not isinstance(arguments, dict):
                    raise ValueError("Tool arguments must be a JSON object.")
                tool_result = execute_tool(tool_name, arguments)
            except (TypeError, ValueError, json.JSONDecodeError):
                tool_result = {"error": "The tool arguments were invalid."}

            tool_outputs.append(
                {
                    "type": "function_call_output",
                    "call_id": tool_call.call_id,
                    "output": json.dumps(tool_result),
                }
            )

        try:
            result = client.responses.create(
                model="gpt-4o-mini",
                previous_response_id=result.id,
                input=tool_outputs,
                instructions=LLM_INSTRUCTIONS,
                tools=TOOL_DEFINITIONS,
            )
        except OpenAIError as error:
            raise LLMServiceError(
                "The language model could not process the tool result."
            ) from error

    raise LLMServiceError("The language model used too many tool calls.")