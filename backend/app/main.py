from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import auth, users
from app.core.config import settings
from app.db.database import Base, engine

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG,
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
