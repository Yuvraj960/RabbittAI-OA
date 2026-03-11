"""Google Gemini AI service for generating sales summaries."""
import google.generativeai as genai
from fastapi import HTTPException, status

from app.core.config import settings

_SYSTEM_PROMPT = """You are an expert business analyst and data scientist at a top-tier consulting firm.
Your role is to analyze sales data and produce a concise, insightful executive brief.
Be professional, precise, and highlight the most impactful trends and actionable recommendations.
Format your response in clean HTML using headings (<h2>, <h3>), paragraphs (<p>), bullet lists (<ul><li>), 
and bold text (<strong>) where appropriate. Do NOT use markdown."""

_USER_PROMPT_TEMPLATE = """Please analyze the following sales dataset and generate a professional executive summary.

The summary must include:
1. **Overview** — Total revenue, total units sold, and date range covered.
2. **Top Performers** — Best-performing product categories and regions.
3. **Trends & Observations** — Notable patterns (growth, seasonality, anomalies).
4. **Risk Areas** — Any cancellations, underperforming segments, or concerns.
5. **Executive Recommendation** — 2–3 actionable next steps for the sales leadership team.

--- DATASET ---
{data_summary}
--- END OF DATASET ---

Produce the HTML report now:"""


def _get_model() -> genai.GenerativeModel:
    """Initialize and return the Gemini model."""
    if not settings.gemini_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gemini API key not configured on the server.",
        )
    genai.configure(api_key=settings.gemini_api_key)
    return genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=_SYSTEM_PROMPT,
    )


async def generate_sales_summary(data_summary: str) -> str:
    """
    Call Google Gemini API with the structured data summary.
    Returns an HTML-formatted executive narrative.
    """
    try:
        model = _get_model()
        prompt = _USER_PROMPT_TEMPLATE.format(data_summary=data_summary)
        response = model.generate_content(prompt)
        return response.text
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI generation failed: {exc}",
        ) from exc
