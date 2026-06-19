from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
from app.database import engine, Base
from app.models import Tenant, User, Log, AlertRule, AlertEvent
from app.routes import auth, logs, alerts
from app.syslog_server import start_syslog_server
from app.config import get_settings

settings = get_settings()

# Create tables
Base.metadata.create_all(bind=engine)

# Syslog server task
syslog_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global syslog_task
    print("Starting syslog server...")
    syslog_task = asyncio.create_task(start_syslog_server())
    yield
    # Shutdown
    print("Shutting down...")
    syslog_task.cancel()

app = FastAPI(
    title="Log Management System API",
    description="Centralized log collection and analysis platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth.router)
app.include_router(logs.router)
app.include_router(alerts.router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/")
async def root():
    return {
        "name": "Log Management System API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
