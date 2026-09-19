"""Human-readable explanations without legal conclusions or prompt values."""

ENTITY_REASONS: dict[str, str] = {
    "TC_ID": "Direct national identity identifier detected.",
    "PASSPORT_ID": "Direct passport identifier detected.",
    "CREDIT_CARD": "Payment card data detected.",
    "IBAN": "Bank account identifier detected.",
    "PHONE": "Contact telephone number detected.",
    "EMAIL": "Contact email address detected.",
    "PERSON": "A person name was detected by the local semantic provider.",
    "LOCATION": "A location name was detected by the local semantic provider.",
    "DATE": "A date value was detected.",
    "IP_ADDRESS": "A network address was detected.",
    "URL": "A URL was detected.",
    "ORGANIZATION": "An organization name was detected by the local semantic provider.",
    "POSSIBLE_TC_ID": "A TC-ID-like value was detected, but its checksum is invalid.",
    "POSSIBLE_PASSPORT_ID": "A passport-context identifier was detected, but its format is unverified.",
    "POSSIBLE_CREDIT_CARD": "A card-shaped value was detected, but its checksum is invalid.",
    "POSSIBLE_IBAN": "An IBAN-like value was detected, but its checksum is invalid.",
}


def reason_for(entity_type: str) -> str:
    return ENTITY_REASONS.get(entity_type, "A supported entity was detected.")
