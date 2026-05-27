from datetime import date

from pydantic import BaseModel


class ExtractionResult(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: date


class DocumentExtractResponse(BaseModel):
    extraction: ExtractionResult
    filename: str
    message: str = "Extraction successful"
