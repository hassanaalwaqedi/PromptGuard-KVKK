"""Normalized API representation of detected sensitive entities."""

from pydantic import BaseModel, Field


class DetectedEntity(BaseModel):
    type: str
    text: str
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    confidence: float = Field(ge=0, le=1)
    source: str
    metadata: dict[str, str] = Field(default_factory=dict)
