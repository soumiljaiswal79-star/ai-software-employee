from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .llm import LLMConfigurationError, LLMServiceError, get_llm_response

app = FastAPI(title="AI Software Employee")


class ChatRequest(BaseModel):
    message: str


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
    except LLMServiceError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error

    return {"response": response, "tools_used": tools_used}