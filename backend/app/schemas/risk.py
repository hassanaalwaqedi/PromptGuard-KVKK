"""Strongly typed Phase 3 risk response models."""

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.entities import DetectedEntity
from app.services.sanitization.policy import SanitizationAction

RiskLevel = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
PolicyDecision = Literal["ALLOW", "WARN", "MASK", "BLOCK"]


class RiskEntity(DetectedEntity):
    category: str
    base_weight: float = Field(ge=0)
    risk_contribution: float = Field(ge=0)
    reason: str
    sanitization_action: SanitizationAction = "KEEP"


class RiskFactor(BaseModel):
    kind: Literal["entity", "sensitivity", "combination", "repetition"]
    rule: str
    message: str
    bonus: float = Field(default=0, ge=0)
    entity_type: str | None = None


class RiskSummary(BaseModel):
    score: int = Field(ge=0, le=100)
    level: RiskLevel
    decision: PolicyDecision


class RiskAssessment(BaseModel):
    entities: list[RiskEntity]
    summary: RiskSummary
    factors: list[RiskFactor]
