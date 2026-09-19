"""Single source of truth for Phase 3 sensitivity weights and rules."""

from __future__ import annotations

from typing import Final

ENTITY_WEIGHTS: Final[dict[str, float]] = {
    "TC_ID": 40.0,
    "PASSPORT_ID": 40.0,
    "CREDIT_CARD": 40.0,
    "IBAN": 32.0,
    "PHONE": 18.0,
    "EMAIL": 15.0,
    "PERSON": 12.0,
    "LOCATION": 10.0,
    "DATE": 6.0,
    "IP_ADDRESS": 12.0,
    "URL": 4.0,
    "ORGANIZATION": 5.0,
    # Suspicious near-matches are intentionally lower-weight warnings. They
    # never receive the direct-identifier combination bonuses below.
    "POSSIBLE_TC_ID": 10.0,
    "POSSIBLE_PASSPORT_ID": 10.0,
    "POSSIBLE_CREDIT_CARD": 10.0,
    "POSSIBLE_IBAN": 8.0,
}

ENTITY_CATEGORIES: Final[dict[str, str]] = {
    "TC_ID": "DIRECT_IDENTIFIER",
    "PASSPORT_ID": "DIRECT_IDENTIFIER",
    "CREDIT_CARD": "FINANCIAL_INFORMATION",
    "IBAN": "FINANCIAL_INFORMATION",
    "PHONE": "CONTACT_INFORMATION",
    "EMAIL": "CONTACT_INFORMATION",
    "IP_ADDRESS": "NETWORK_IDENTIFIER",
    "PERSON": "PERSONAL_INFORMATION",
    "LOCATION": "PERSONAL_INFORMATION",
    "DATE": "PERSONAL_INFORMATION",
    "URL": "OTHER",
    "ORGANIZATION": "OTHER",
    "POSSIBLE_TC_ID": "SUSPICIOUS_IDENTIFIER",
    "POSSIBLE_PASSPORT_ID": "SUSPICIOUS_IDENTIFIER",
    "POSSIBLE_CREDIT_CARD": "SUSPICIOUS_IDENTIFIER",
    "POSSIBLE_IBAN": "SUSPICIOUS_IDENTIFIER",
}

# Additive, bounded bonuses. They are deliberately not multipliers so that a
# prompt with repeated data cannot grow without an upper bound.
DIRECT_IDENTIFIER_EXPOSURE_BONUS: Final[float] = 15.0
DIRECT_IDENTIFIER_CONTACT_BONUS: Final[float] = 12.0
DIRECT_IDENTIFIER_FINANCIAL_BONUS: Final[float] = 15.0
FINANCIAL_CONTACT_BONUS: Final[float] = 8.0
THREE_CATEGORY_DIVERSITY_BONUS: Final[float] = 8.0
REPEATED_ENTITY_BONUS: Final[float] = 3.0
SUSPICIOUS_IDENTIFIER_REVIEW_BONUS: Final[float] = 18.0

LOW_MAX: Final[int] = 20
MEDIUM_MAX: Final[int] = 45
HIGH_MAX: Final[int] = 70
MAX_RISK_SCORE: Final[int] = 100


def category_for(entity_type: str) -> str:
    return ENTITY_CATEGORIES.get(entity_type, "OTHER")


def weight_for(entity_type: str) -> float:
    return ENTITY_WEIGHTS.get(entity_type, 0.0)


def risk_level_for_score(score: int | float) -> str:
    """Map a clamped score to the documented, inclusive risk boundaries."""
    if score <= LOW_MAX:
        return "LOW"
    if score <= MEDIUM_MAX:
        return "MEDIUM"
    if score <= HIGH_MAX:
        return "HIGH"
    return "CRITICAL"
