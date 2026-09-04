import os

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError

load_dotenv()


class LLMConfigurationError(RuntimeError):
    """Raised when the LLM is not configured."""


class LLMServiceError(RuntimeError):
    """Raised when the LLM cannot return a response."""


def get_llm_response(message: str) -> str:
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
        )
    except OpenAIError as error:
        raise LLMServiceError("The language model could not process the request.") from error

    return result.output_text