# backend/main.py (or backend/app/main.py)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import auth, tasks, users
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="Backend API for PrimeTradeAI Internship Assignment",
    version="1.0.0",
)

# ── CORS Middleware ──────────────────────────────────────────
# This allows your React frontend (e.g., localhost:5173) to 
# communicate with this backend securely.
if settings.BACKEND_CORS_ORIGINS:
    allowed_origins = [str(origin).rstrip("/") for origin in settings.BACKEND_CORS_ORIGINS]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# ── Router Registration ──────────────────────────────────────
# Notice we prefix everything with /api/v1 automatically
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(users.router, prefix=settings.API_V1_STR)
app.include_router(tasks.router, prefix=settings.API_V1_STR)

@app.get("/", tags=["Health"])
def health_check():
    """Simple health check endpoint to verify the API is running."""
    return {"status": "ok", "message": "PrimeTradeAI API is running smoothly!"}
