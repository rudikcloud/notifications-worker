from fastapi import FastAPI

from app.config import get_settings

app = FastAPI(title="RudikCloud Notifications Worker")


@app.get("/health")
def health() -> dict[str, str]:
    get_settings()
    return {"status": "ok"}
