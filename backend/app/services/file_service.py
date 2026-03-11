"""File parsing and validation service."""
import io
from typing import Tuple

import pandas as pd
from fastapi import UploadFile, HTTPException, status

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}
ALLOWED_MIME_TYPES = {
    "text/csv",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/octet-stream",  # some browsers send this for xlsx
}
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


async def parse_upload(file: UploadFile) -> Tuple[pd.DataFrame, str]:
    """
    Validate and parse an uploaded CSV/XLSX file into a DataFrame.
    Returns (dataframe, file_extension).
    Raises HTTPException on invalid input.
    """
    # --- Validate filename extension ---
    filename = file.filename or ""
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'. Please upload a .csv or .xlsx file.",
        )

    # --- Read content and enforce size limit ---
    content = await file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds {MAX_FILE_SIZE_MB}MB limit.",
        )
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    # --- Parse into DataFrame ---
    try:
        if ext == ".csv":
            df = pd.read_csv(io.BytesIO(content))
        else:
            df = pd.read_excel(io.BytesIO(content), engine="openpyxl")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not parse file: {exc}",
        ) from exc

    if df.empty:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file contains no data rows.",
        )

    return df, ext


def build_data_summary(df: pd.DataFrame) -> str:
    """Convert a DataFrame into a structured text summary for the AI prompt."""
    lines = []
    lines.append(f"Dataset shape: {df.shape[0]} rows × {df.shape[1]} columns")
    lines.append(f"Columns: {', '.join(df.columns.tolist())}")
    lines.append("")

    # Numeric column statistics
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if numeric_cols:
        lines.append("=== Numeric Summary ===")
        lines.append(df[numeric_cols].describe().to_string())
        lines.append("")

    # Categorical breakdown
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    for col in cat_cols[:5]:  # limit to first 5 categorical cols
        vc = df[col].value_counts().head(10)
        lines.append(f"=== {col} Breakdown ===")
        lines.append(vc.to_string())
        lines.append("")

    # First 10 rows of data
    lines.append("=== Sample Data (first 10 rows) ===")
    lines.append(df.head(10).to_string(index=False))

    return "\n".join(lines)
