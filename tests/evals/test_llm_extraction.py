"""
LLM extraction evals using deepeval.

These tests validate the quality of the LLM extraction, not just its structure.
They require OPENAI_API_KEY and are slower than unit/integration tests.

Run with:  pytest -m eval tests/evals/
Skip with: pytest -m "not eval"
"""

import pytest

# deepeval imports are deferred inside tests so the module can be collected
# even if the import fails in a CI environment that skips evals.


@pytest.mark.eval
async def test_extraction_returns_all_fields():
    """The LLM must return first_name, last_name, and date_of_birth — never partial."""
    from app.services.llm_service import extract_patient_info

    with open("DME Patient Demo Document CPAP.fax.pdf", "rb") as f:
        pdf_bytes = f.read()

    result = await extract_patient_info(pdf_bytes)

    assert result.first_name, "first_name must be non-empty"
    assert result.last_name, "last_name must be non-empty"
    assert result.date_of_birth, "date_of_birth must be non-empty"


@pytest.mark.eval
async def test_extraction_accuracy_with_deepeval():
    """
    Semantic accuracy test: deepeval GEval judges whether the extracted
    fields are plausible for a medical fax document.
    """
    from deepeval import assert_test
    from deepeval.metrics import GEval, LLMTestCaseParams
    from deepeval.test_case import LLMTestCase

    from app.services.llm_service import extract_patient_info

    with open("DME Patient Demo Document CPAP.fax.pdf", "rb") as f:
        pdf_bytes = f.read()

    result = await extract_patient_info(pdf_bytes)

    test_case = LLMTestCase(
        input="Extract the patient's first name, last name, and date of birth from the medical fax PDF.",
        actual_output=(
            f"first_name={result.first_name}, "
            f"last_name={result.last_name}, "
            f"date_of_birth={result.date_of_birth}"
        ),
    )

    completeness_metric = GEval(
        name="Extraction Completeness",
        criteria=(
            "The output contains all three fields (first_name, last_name, date_of_birth). "
            "Names look like real human names. Date of birth is a plausible past date."
        ),
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT],
        threshold=0.8,
    )

    assert_test(test_case, [completeness_metric])


@pytest.mark.eval
async def test_extraction_does_not_hallucinate_missing_fields():
    """
    When a field is absent in the document, the LLM must not invent a value.
    Uses a minimal text-only PDF stub that contains only a first name.
    """
    from deepeval import assert_test
    from deepeval.metrics import GEval, LLMTestCaseParams
    from deepeval.test_case import LLMTestCase

    from app.services.llm_service import extract_patient_info

    # Minimal PDF bytes that encode a text-only page with no last name or DOB
    # If the service returns empty/null for missing fields instead of a hallucinated value,
    # this test passes. Adjust expected_output once the real extraction contract is defined.
    minimal_pdf = _make_minimal_pdf(b"Patient: John")

    result = await extract_patient_info(minimal_pdf)

    test_case = LLMTestCase(
        input="Extract patient info from a document that only contains 'Patient: John'.",
        actual_output=(
            f"first_name={result.first_name}, "
            f"last_name={result.last_name}, "
            f"date_of_birth={result.date_of_birth}"
        ),
        expected_output="first_name=John, last_name=unknown or empty, date_of_birth=unknown or empty",
    )

    no_hallucination_metric = GEval(
        name="No Hallucination",
        criteria=(
            "When the source document does not contain a last name or date of birth, "
            "the extraction must not invent plausible-sounding but fabricated values."
        ),
        evaluation_params=[
            LLMTestCaseParams.INPUT,
            LLMTestCaseParams.ACTUAL_OUTPUT,
            LLMTestCaseParams.EXPECTED_OUTPUT,
        ],
        threshold=0.7,
    )

    assert_test(test_case, [no_hallucination_metric])


def _make_minimal_pdf(text: bytes) -> bytes:
    """Build a syntactically valid minimal PDF containing only the given text."""
    content = (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Contents 4 0 R>>endobj\n"
    )
    stream = b"BT /F1 12 Tf 72 720 Td (" + text + b") Tj ET"
    content += (
        b"4 0 obj<</Length " + str(len(stream)).encode() + b">>\nstream\n"
        + stream + b"\nendstream\nendobj\n"
        b"xref\n0 5\n"
        b"0000000000 65535 f\r\n"
        b"trailer<</Size 5/Root 1 0 R>>\n"
        b"startxref\n9\n%%EOF"
    )
    return content
