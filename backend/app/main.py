from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.database import init_db
from app.schemas import HealthResponse

app = FastAPI(
    title="Event Quality Dashboard API",
    description="Academic MVP API for synthetic event quality monitoring and anomaly detection.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/")
def read_root():
    return {
        "name": "Event Quality Dashboard API",
        "status": "ready",
        "docs": "/docs",
    }


@app.get("/health", response_model=HealthResponse)
def root_health_check():
    return HealthResponse(status="ok", service="event-quality-dashboard-api")
