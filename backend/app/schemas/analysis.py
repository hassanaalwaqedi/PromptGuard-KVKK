"""Schemas for the in-memory Phase 3 analysis endpoint."""

from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.schemas.risk import RiskEntity, RiskFactor, RiskSummary


class AnalyzeRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=10_000)

    @field_validator("prompt")
    @classmethod
    def prompt_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Prompt must not be empty.")
        return value


class AnalyzeResponse(BaseModel):
    analysis_id: UUID
    entity_count: int = Field(ge=0)
    entities: list[RiskEntity]
    status: str
    ner_available: bool
    ner_provider: str
    risk: RiskSummary
    risk_factors: list[RiskFactor]
    sanitized_prompt: str
