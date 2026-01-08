from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import auth, users
from app.core.config import settings
from app.db.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup: Create database tables (skip in test mode)
    if not os.getenv("TESTING"):
        Base.metadata.create_all(bind=engine)
    yield
    # Shutdown: cleanup if needed


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": f"Welcome to {settings.APP_NAME}"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}
