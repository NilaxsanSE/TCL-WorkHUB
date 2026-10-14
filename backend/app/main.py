from fastapi import FastAPI

from app.config import settings

app = FastAPI(title=settings.project_name)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "backend",
        "environment": settings.environment,
    }

