from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.auth.auth_router import router as auth_router
from core.config import settings
from database import get_db

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/db-check")
async def db_check():
    async for db in get_db():
        await db.execute(text("SELECT 1"))
        return {"db_status": "ok"}
    return {"db_status": "error"}
