"""Shared types for detection services."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DetectionCandidate:
    """An internal entity candidate whose offsets refer to the original prompt."""

    type: str
    text: str
    start: int
    end: int
    confidence: float
    source: str
    metadata: dict[str, str] = field(default_factory=dict)
