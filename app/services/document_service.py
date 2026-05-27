import io
import json
from datetime import date

import openai
from fastapi import HTTPException, UploadFile, status
from openai import AsyncOpenAI
from pypdf import PdfReader

from app.core.config import settings
from app.schemas.document import DocumentExtractResponse, ExtractionResult

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

_SYSTEM = (
    "You are a medical document parser. Extract the patient's first name, last name, "
    "and date of birth from the provided text. "
    'Return ONLY a JSON object with keys "first_name" (string), "last_name" (string), '
    '"date_of_birth" (ISO date YYYY-MM-DD). Use null for any field not found.'
)


def _get_client() -> AsyncOpenAI:
    return AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


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
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not parse PDF")

    try:
        response = await _get_client().chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": text[:8000]},
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

    return DocumentExtractResponse(
        extraction=ExtractionResult(
            first_name=data["first_name"],
            last_name=data["last_name"],
            date_of_birth=dob,
        ),
        filename=file.filename or "unknown",
    )
