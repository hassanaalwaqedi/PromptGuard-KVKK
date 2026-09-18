"""Deterministic policy mapping for risk levels."""

from typing import Final

POLICY_BY_LEVEL: Final[dict[str, str]] = {
    "LOW": "ALLOW",
    "MEDIUM": "WARN",
    "HIGH": "MASK",
    "CRITICAL": "BLOCK",
}


def policy_for_level(level: str) -> str:
    return POLICY_BY_LEVEL.get(level, "BLOCK")
