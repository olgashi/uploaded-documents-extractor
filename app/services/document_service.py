import base64
import io
import json
from datetime import date
from pathlib import Path

import fitz  # pymupdf
import openai
from fastapi import HTTPException, UploadFile, status
from openai import AsyncOpenAI
from pypdf import PdfReader

from app.core.config import settings
from app.schemas.document import DocumentExtractResponse, ExtractionResult

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

_SYSTEM = (
    "You are a medical document parser. Extract the patient's first name, last name, "
    "and date of birth from the provided document. "
    'Return ONLY a JSON object with keys "first_name" (string), "last_name" (string), '
    '"date_of_birth" (ISO date YYYY-MM-DD). Use null for any field not found.'
)


def _get_client() -> AsyncOpenAI:
    return AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


def _pdf_to_images(content: bytes) -> list[str]:
    """Render each PDF page to a base64-encoded PNG. Returns up to 3 pages."""
    doc = fitz.open(stream=content, filetype="pdf")
    images = []
    for i, page in enumerate(doc):
        if i >= 3:
            break
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        images.append(base64.b64encode(pix.tobytes("png")).decode())
    doc.close()
    return images


async def extract_from_pdf(file: UploadFile) -> DocumentExtractResponse:
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File must be a PDF")

    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File exceeds 10 MB limit",
        )

    try:
        reader = PdfReader(io.BytesIO(content))
        text = "\n".join(page.extract_text() or "" for page in reader.pages).strip()
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not parse PDF")

    # Use vision API for scanned PDFs (no text layer), text API otherwise
    if text:
        user_content: list | str = text[:8000]
    else:
        try:
            images = _pdf_to_images(content)
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not parse PDF")
        user_content = [
            *[
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{img}", "detail": "high"},
                }
                for img in images
            ],
            {"type": "text", "text": "Extract the patient information from this document."},
        ]

    try:
        response = await _get_client().chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": user_content},
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )
    except openai.AuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Extraction service is not configured. Contact support.",
        )
    except openai.RateLimitError:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Extraction service is busy. Please try again shortly.",
        )
    except openai.APIConnectionError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not reach extraction service. Please try again.",
        )
    except openai.APIError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Extraction service returned an error. Please try again.",
        )

    data = json.loads(response.choices[0].message.content)

    dob_raw = data.get("date_of_birth")
    try:
        dob = date.fromisoformat(dob_raw) if dob_raw else None
    except (ValueError, TypeError):
        dob = None

    if not data.get("first_name") or not data.get("last_name") or dob is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not extract all required fields from document",
        )

    raw_filename = file.filename or "unknown"
    safe_filename = (Path(raw_filename).name or "unknown")[:255]

    return DocumentExtractResponse(
        extraction=ExtractionResult(
            first_name=data["first_name"],
            last_name=data["last_name"],
            date_of_birth=dob,
        ),
        filename=safe_filename,
    )
