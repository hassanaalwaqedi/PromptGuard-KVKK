"""Pure validation functions for structured sensitive identifiers."""

from datetime import date
import re

from app.services.detection.normalization import compact_identifier


def is_valid_tc_id(value: str) -> bool:
    """Validate the public checksum rules of a Turkish T.C. Kimlik number."""
    if not re.fullmatch(r"[1-9]\d{10}", value):
        return False
    if len(set(value[:9])) == 1:
        return False

    digits = [int(char) for char in value]
    tenth_digit = ((sum(digits[0:9:2]) * 7) - sum(digits[1:8:2])) % 10
    eleventh_digit = sum(digits[:10]) % 10
    return digits[9] == tenth_digit and digits[10] == eleventh_digit


def is_valid_turkish_iban(value: str) -> bool:
    """Validate a Turkish IBAN with the ISO 13616 MOD-97 checksum."""
    iban = compact_identifier(value).upper()
    if not re.fullmatch(r"TR\d{24}", iban):
        return False

    rearranged = iban[4:] + iban[:4]
    numeric = "".join(str(ord(char) - 55) if char.isalpha() else char for char in rearranged)
    return int(numeric) % 97 == 1


def is_valid_luhn(value: str) -> bool:
    """Validate likely payment card digits using the Luhn algorithm."""
    digits = compact_identifier(value)
    if not digits.isdigit() or not 13 <= len(digits) <= 19 or len(set(digits)) == 1:
        return False

    checksum = 0
    for index, char in enumerate(reversed(digits)):
        digit = int(char)
        if index % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit
    return checksum % 10 == 0


def is_valid_ipv4(value: str) -> bool:
    """Validate IPv4 octets without accepting shortened or out-of-range forms."""
    parts = value.split(".")
    return len(parts) == 4 and all(part.isdigit() and 0 <= int(part) <= 255 for part in parts)


def is_valid_date(value: str) -> bool:
    """Validate supported Turkish/European and ISO date formats."""
    try:
        if "-" in value:
            year, month, day = (int(part) for part in value.split("-"))
        else:
            separator = "." if "." in value else "/"
            day, month, year = (int(part) for part in value.split(separator))
        date(year, month, day)
    except (TypeError, ValueError):
        return False
    return True
