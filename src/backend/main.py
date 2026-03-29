"""
Veluga PDF Parser — FastAPI application entry point.
"""
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Ensure project root is on sys.path so 'src.backend' imports resolve
# regardless of which directory uvicorn is launched from.
_project_root = str(Path(__file__).resolve().parent.parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.backend.database import create_tables
from src.backend.routes.upload import router as upload_router
from src.backend.routes.jobs import router as jobs_router
from src.backend.routes.results import router as results_router
from src.backend.routes.settings import router as settings_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield


app = FastAPI(title="Veluga PDF Parser", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(upload_router, prefix="/api")
app.include_router(jobs_router, prefix="/api")
app.include_router(results_router, prefix="/api")
app.include_router(settings_router, prefix="/api")

# Serve React frontend in production (if dist/ exists)
_frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if _frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(_frontend_dist), html=True), name="frontend")
