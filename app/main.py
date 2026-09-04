from fastapi import FastAPI

app = FastAPI(title="AI Software Employee")


@app.get("/")
def get_status() -> dict[str, str]:
    return {
        "employee": "AI Software Employee",
        "status": "online",
    }