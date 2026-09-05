from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .agent import run_software_task
from .llm import (
    LLMAuthenticationError,
    LLMConfigurationError,
    LLMRateLimitError,
    LLMServiceError,
    get_llm_response,
)
from .tools.git import (
    git_diff,
    git_init,
    git_status,
    git_create_branch,
)

app = FastAPI(title="AI Software Employee")


class ChatRequest(BaseModel):
    message: str


class TaskRequest(BaseModel):
    task: str


@app.get("/")
def get_status() -> dict[str, str]:
    return {
        "employee": "AI Software Employee",
        "status": "online",
    }


@app.post("/chat")
def chat(request: ChatRequest) -> dict[str, object]:
    try:
        response, tools_used = get_llm_response(request.message)
    except LLMConfigurationError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except LLMAuthenticationError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    except LLMRateLimitError as error:
        raise HTTPException(status_code=429, detail=str(error)) from error
    except LLMServiceError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error

    return {
        "response": response,
        "tools_used": tools_used,
    }


@app.post("/task")
def task(request: TaskRequest) -> dict[str, object]:
    try:
        state = run_software_task(request.task)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except LLMConfigurationError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except LLMAuthenticationError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    except LLMRateLimitError as error:
        raise HTTPException(status_code=429, detail=str(error)) from error
    except LLMServiceError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error

    result = state.to_dict()
    result["iterations"] = state.current_iteration
    result["response"] = state.final_message

    return result


@app.get("/debug/git")
def debug_git() -> dict[str, object]:
    """Test Git tools without using Gemini."""
    results: dict[str, object] = {}

    results["init"] = git_init()

    results["status_after_init"] = git_status()

    results["create_branch"] = git_create_branch("test/git-integration")

    results["status_after_branch"] = git_status()

    results["diff"] = git_diff()

    return results
