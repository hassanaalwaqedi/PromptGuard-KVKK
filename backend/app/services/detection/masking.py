"""Reusable presentation masking utilities; prompts are never modified here."""

import re

from app.services.detection.normalization import compact_identifier


def mask_entity(entity_type: str, value: str) -> str:
    """Return a display-safe representation of an entity value."""
    if entity_type == "PHONE":
        digits = re.sub(r"\D", "", value)
        if digits.startswith("90") and len(digits) == 12:
            return "+90 *** *** ** **"
        if len(digits) == 11 and digits.startswith("0"):
            return "0*** *** ** **"
        return "*** *** ** **"
    if entity_type == "EMAIL" and "@" in value:
        local, domain = value.split("@", 1)
        return f"{local[:1]}*****@{domain}"
    if entity_type == "TC_ID" and len(value) == 11:
        return f"{value[:3]}*******{value[-2:]}"
    if entity_type == "IBAN":
        compact = compact_identifier(value)
        return f"{compact[:4]}{'*' * (len(compact) - 6)}{compact[-2:]}"
    if entity_type == "CREDIT_CARD":
        compact = compact_identifier(value)
        return f"{'*' * max(0, len(compact) - 4)}{compact[-4:]}"
    return value
