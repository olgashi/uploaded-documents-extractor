"""Document extraction tests."""

import io
from datetime import date

import pytest

from app.schemas.document import DocumentExtractResponse, ExtractionResult


@pytest.mark.eval
@pytest.mark.integration
async def test_extract_pdf_returns_patient_info(authed_client):
    """Upload the sample PDF and expect all three fields back."""
    with open("DME Patient Demo Document CPAP.fax.pdf", "rb") as f:
        pdf_bytes = f.read()

    response = await authed_client.post(
        "/api/v1/documents/extract",
        files={"file": ("sample.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 200
    body = response.json()
    extraction = body["extraction"]
    assert extraction["first_name"]
    assert extraction["last_name"]
    assert extraction["date_of_birth"]


@pytest.mark.eval
@pytest.mark.integration
async def test_extract_returns_valid_date_format(authed_client):
    with open("DME Patient Demo Document CPAP.fax.pdf", "rb") as f:
        pdf_bytes = f.read()

    response = await authed_client.post(
        "/api/v1/documents/extract",
        files={"file": ("sample.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 200
    dob = response.json()["extraction"]["date_of_birth"]
    # Must be a valid ISO date string
    from datetime import date
    date.fromisoformat(dob)


@pytest.mark.integration
async def test_extract_non_pdf_returns_400(authed_client):
    fake_txt = io.BytesIO(b"not a pdf")
    response = await authed_client.post(
        "/api/v1/documents/extract",
        files={"file": ("document.txt", fake_txt, "text/plain")},
    )
    assert response.status_code == 400


@pytest.mark.integration
async def test_extract_missing_file_returns_422(authed_client):
    response = await authed_client.post("/api/v1/documents/extract")
    assert response.status_code == 422


@pytest.mark.integration
async def test_extract_oversized_file_returns_413(authed_client):
    # 11 MB of zeros — above the 10 MB limit
    big_file = io.BytesIO(b"\x00" * (11 * 1024 * 1024))
    response = await authed_client.post(
        "/api/v1/documents/extract",
        files={"file": ("big.pdf", big_file, "application/pdf")},
    )
    assert response.status_code == 413


@pytest.mark.integration
async def test_upload_order_creates_order(authed_client, monkeypatch):
    async def fake_extract(file):
        return DocumentExtractResponse(
            extraction=ExtractionResult(
                first_name="Jane",
                last_name="Doe",
                date_of_birth=date(1985, 6, 15),
            ),
            filename=file.filename,
        )

    monkeypatch.setattr("app.services.document_service.extract_from_pdf", fake_extract)

    pdf = io.BytesIO(b"%PDF-1.4 fake")
    response = await authed_client.post(
        "/api/v1/documents/upload-order",
        files={"file": ("patient.pdf", pdf, "application/pdf")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["patient_first_name"] == "Jane"
    assert body["patient_last_name"] == "Doe"
    assert body["patient_dob"] == "1985-06-15"
    assert body["document_filename"] == "patient.pdf"


@pytest.mark.integration
async def test_upload_order_same_document_returns_existing_order(authed_client, monkeypatch):
    async def fake_extract(file):
        return DocumentExtractResponse(
            extraction=ExtractionResult(
                first_name="Jane",
                last_name="Doe",
                date_of_birth=date(1985, 6, 15),
            ),
            filename=file.filename,
        )

    monkeypatch.setattr("app.services.document_service.extract_from_pdf", fake_extract)

    first_response = await authed_client.post(
        "/api/v1/documents/upload-order",
        files={"file": ("patient.pdf", io.BytesIO(b"%PDF-1.4 fake"), "application/pdf")},
    )
    second_response = await authed_client.post(
        "/api/v1/documents/upload-order",
        files={"file": ("patient.pdf", io.BytesIO(b"%PDF-1.4 fake"), "application/pdf")},
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 200
    assert second_response.json()["id"] == first_response.json()["id"]

    list_response = await authed_client.get("/api/v1/orders")
    assert list_response.json()["total"] == 1
