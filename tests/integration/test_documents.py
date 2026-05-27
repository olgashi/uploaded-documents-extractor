"""Document extraction tests — will fail (501) until LLM service is implemented."""

import io

import pytest


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
