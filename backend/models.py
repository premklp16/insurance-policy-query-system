from pydantic import BaseModel, Field, field_validator

class QueryRequest(BaseModel):
    question: str = Field(..., description="The query question to search in the policy PDF.")

    @field_validator("question")
    @classmethod
    def validate_question(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Question cannot be empty or contain only whitespace.")
        return cleaned

from typing import Optional

class QueryResponse(BaseModel):
    status: str = Field(..., description="The retrieval status ('success' or 'error').")
    answer: Optional[str] = Field(None, description="The most relevant paragraph retrieved from the policy document.")
    page: Optional[int] = Field(None, description="The 1-based page number where the section is located.")
    similarity: float = Field(..., description="The cosine similarity percentage matching score (0.0 to 100.0).")
    message: Optional[str] = Field(None, description="Informative message if needed.")
    highlighted_sentence: Optional[str] = Field(None, description="The most relevant sentence within the answer chunk.")
    heading: Optional[str] = Field(None, description="The heading label of the matched section.")

class HealthResponse(BaseModel):
    status: str = Field(..., description="The operational status of the service (typically 'ok').")
    model_loaded: bool = Field(..., description="Flag indicating whether the Sentence Transformers model is loaded in memory.")
    document_uploaded: bool = Field(..., description="Flag indicating whether a valid policy document is currently uploaded and active in the cache.")
