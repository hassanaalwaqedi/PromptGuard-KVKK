"""Small normalization helpers that never alter response offsets."""

import re


def compact_identifier(value: str) -> str:
    """Remove presentation separators from an identifier before validation."""
    return re.sub(r"[\s-]", "", value)


def normalize_phone(value: str) -> str | None:
    """Return a canonical Turkish mobile number when it has a valid shape."""
    digits = re.sub(r"\D", "", value)
    if digits.startswith("0090"):
        digits = "0" + digits[4:]
    elif digits.startswith("90") and len(digits) == 12:
        digits = "0" + digits[2:]
    elif len(digits) == 10 and digits.startswith("5"):
        digits = "0" + digits

    if len(digits) == 11 and digits.startswith("05"):
        return digits
    return None
