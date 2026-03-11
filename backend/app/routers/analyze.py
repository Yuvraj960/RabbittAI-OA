"""Analyze router — POST /api/analyze endpoint."""
import re
from typing import Annotated

from fastapi import APIRouter, Depends, Form, UploadFile, File, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.security import get_api_key
from app.services.file_service import parse_upload, build_data_summary
from app.services.ai_service import generate_sales_summary
from app.services.email_service import send_summary_email

router = APIRouter(prefix="/api", tags=["Analysis"])
limiter = Limiter(key_func=get_remote_address)

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@router.post(
    "/analyze",
    summary="Upload & Analyze Sales Data",
    description=(
        "Upload a **CSV or XLSX** file containing sales data along with a recipient email address. "
        "The endpoint will parse the file, generate an AI-written executive summary using Google Gemini, "
        "and deliver it to the provided email inbox.\n\n"
        "**Authentication:** Requires a valid `X-API-Key` header."
    ),
    response_description="Success confirmation with a status message.",
    responses={
        200: {"description": "Summary generated and email sent successfully."},
        400: {"description": "Invalid file type, empty file, or bad email address."},
        403: {"description": "Missing or invalid API key."},
        413: {"description": "File exceeds 10MB size limit."},
        422: {"description": "File could not be parsed."},
        502: {"description": "AI generation upstream error."},
        503: {"description": "Email service or AI service misconfigured."},
    },
)
@limiter.limit("10/minute")
async def analyze_sales_data(
    request: Request,
    file: Annotated[UploadFile, File(description="CSV or XLSX sales data file (max 10MB)")],
    email: Annotated[str, Form(description="Recipient email address for the generated report")],
    background_tasks: BackgroundTasks,
    _: str = Depends(get_api_key),
) -> JSONResponse:
    # Validate email format
    if not _EMAIL_RE.match(email.strip()):
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "Invalid email address format."},
        )

    # Parse file → DataFrame
    df, ext = await parse_upload(file)
    data_summary = build_data_summary(df)

    # Generate AI summary  
    ai_summary = await generate_sales_summary(data_summary)

    # Send email (in background to avoid blocking response)
    filename = file.filename or f"upload{ext}"
    background_tasks.add_task(send_summary_email, email.strip(), filename, ai_summary)

    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "message": (
                f"Analysis complete! An executive summary for '{filename}' "
                f"has been sent to {email.strip()}."
            ),
        },
    )


@router.get(
    "/health",
    summary="Health Check",
    description="Returns service status. Used by Docker health checks and uptime monitors.",
    tags=["Health"],
)
async def health_check() -> dict:
    return {"status": "healthy", "service": "Rabbitt AI Sales Insight Automator"}
