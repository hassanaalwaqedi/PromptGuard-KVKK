"""Centralized, presentation-only sanitization policy."""

from typing import Final, Literal

SanitizationAction = Literal["KEEP", "PSEUDONYMIZE", "MASK"]

SANITIZATION_POLICY: Final[dict[str, SanitizationAction]] = {
    "TC_ID": "MASK",
    "PASSPORT_ID": "MASK",
    "CREDIT_CARD": "MASK",
    "IBAN": "MASK",
    "PHONE": "MASK",
    "EMAIL": "MASK",
    "IP_ADDRESS": "MASK",
    "PERSON": "PSEUDONYMIZE",
    "LOCATION": "KEEP",
    "ORGANIZATION": "KEEP",
    "DATE": "KEEP",
    "URL": "KEEP",
}


def action_for(entity_type: str) -> SanitizationAction:
    """Unknown future entity types remain visible until explicitly classified."""
    return SANITIZATION_POLICY.get(entity_type, "KEEP")
