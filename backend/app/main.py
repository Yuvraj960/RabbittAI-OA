"""FastAPI application entry point."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.config import settings
from app.routers.analyze import router as analyze_router

# --- Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Rate Limiter ---
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🐇 Rabbitt AI Sales Insight Automator starting up...")
    yield
    logger.info("🐇 Rabbitt AI Sales Insight Automator shutting down...")


# --- FastAPI App ---
app = FastAPI(
    title="Rabbitt AI — Sales Insight Automator",
    description=(
        "## 🐇 Rabbitt AI Sales Insight Automator\n\n"
        "Upload a CSV or XLSX sales file and receive an AI-generated executive summary "
        "delivered directly to your inbox.\n\n"
        "### Authentication\n"
        "All `/api/*` endpoints require an `X-API-Key` header.\n"
        "Include it in every request: `X-API-Key: <your_secret_key>`\n\n"
        "### Rate Limiting\n"
        "Upload endpoint is limited to **10 requests per minute per IP**.\n\n"
        "### Supported File Types\n"
        "`.csv`, `.xlsx`, `.xls` — maximum **10 MB**"
    ),
    version="1.0.0",
    contact={"name": "Rabbitt AI Engineering", "email": "engineering@rabbitt.ai"},
    license_info={"name": "Private — Internal Use Only"},
    lifespan=lifespan,
    swagger_ui_parameters={"syntaxHighlight.theme": "monokai", "docExpansion": "list"},
)

# --- State for rate limiter ---
app.state.limiter = limiter

# --- Security Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"],
)

# Only enforce trusted hosts in production (skip in Docker/dev)
# app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

# --- Exception Handlers ---
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(status.HTTP_422_UNPROCESSABLE_ENTITY)
async def validation_exception_handler(request: Request, exc):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"success": False, "message": "Request validation error.", "details": str(exc)},
    )


@app.exception_handler(500)
async def internal_server_error_handler(request: Request, exc: Exception):
    logger.error(f"Internal server error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "An unexpected error occurred. Please try again."},
    )


# --- Routes ---
app.include_router(analyze_router)


@app.get("/", include_in_schema=False)
async def root():
    return {
        "service": "Rabbitt AI Sales Insight Automator",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health",
    }
