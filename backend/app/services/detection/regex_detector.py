"""Deterministic structured-PII detectors backed by small validators."""

import re

import phonenumbers
from phonenumbers import Leniency, PhoneNumberFormat, PhoneNumberMatcher

from app.services.detection.base import DetectionCandidate
from app.services.detection.normalization import compact_identifier
from app.services.detection.validators import (
    is_valid_date,
    is_valid_ipv4,
    is_valid_luhn,
    is_valid_tc_id,
    is_valid_turkish_iban,
)


class RegexDetector:
    """Detect structured sensitive values while retaining original text spans."""

    tc_id_pattern = re.compile(r"(?<!\d)\d{11}(?!\d)")
    # Kept as a compatibility attribute for callers that used the original
    # Turkish-only detector. PhoneNumberMatcher is now the implementation.
    phone_pattern = re.compile(
        r"(?<![\w+])(?:(?:\+90|0090|0)[\s-]*)?\(?5\d{2}\)?[\s-]*\d{3}[\s-]*\d{2}[\s-]*\d{2}(?!\w)"
    )
    email_pattern = re.compile(
        r"(?<![\w.+-])[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}(?![\w-])",
        re.IGNORECASE,
    )
    iban_pattern = re.compile(
        r"(?<![A-Z0-9])TR(?:[\s-]*\d){24}(?![A-Z0-9])",
        re.IGNORECASE,
    )
    card_pattern = re.compile(r"(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)")
    ipv4_pattern = re.compile(r"(?<!\d)(?:\d{1,3}\.){3}\d{1,3}(?!\d)")
    url_pattern = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)
    date_pattern = re.compile(
        r"(?<!\d)(?:\d{1,2}[./]\d{1,2}[./]\d{4}|\d{4}-\d{1,2}-\d{1,2})(?!\d)"
    )
    passport_pattern = re.compile(
        r"\b(?:passport|pasaport|travel\s+document)\b"
        r"(?:\s+(?:id|number|no|numaras[ıi]|numarasi))?\s*[:#-]?\s*"
        r"(?:(?:was|is|number|no)\s*[:#-]?\s*)?"
        r"(?P<value>[A-Z0-9][A-Z0-9-]{3,14})\b",
        re.IGNORECASE,
    )

    def detect(self, text: str) -> list[DetectionCandidate]:
        entities: list[DetectionCandidate] = []
        entities.extend(self._detect_tc_ids(text))
        phone_entities = self._detect_phones(text)
        phone_spans = [(entity.start, entity.end) for entity in phone_entities]
        entities.extend(phone_entities)
        entities.extend(self._detect_emails(text))
        entities.extend(self._detect_ibans(text))
        entities.extend(self._detect_cards(text))
        entities.extend(self._detect_ips(text))
        entities.extend(self._detect_urls(text))
        entities.extend(self._detect_dates(text))
        entities.extend(self._detect_passports(text))
        entities.extend(self._detect_suspicious_tc_ids(text, phone_spans))
        entities.extend(self._detect_suspicious_ibans(text))
        entities.extend(self._detect_suspicious_cards(text, phone_spans))
        return entities

    def _detect_tc_ids(self, text: str) -> list[DetectionCandidate]:
        return [
            self._candidate("TC_ID", match, 0.99)
            for match in self.tc_id_pattern.finditer(text)
            if is_valid_tc_id(match.group())
        ]

    def _detect_phones(self, text: str) -> list[DetectionCandidate]:
        entities: list[DetectionCandidate] = []
        for match in PhoneNumberMatcher(text, "TR", leniency=Leniency.POSSIBLE):
            raw_value = match.raw_string
            if (
                (match.start > 0 and text[match.start - 1].isalnum())
                or (match.end < len(text) and text[match.end].isalnum())
            ):
                # Do not extract a digit substring from an identifier such as
                # the numeric portion of a passport value.
                continue
            # PhoneNumberMatcher can interpret dotted IPv4 values as a local
            # number. Let the dedicated IPv4 detector own those spans.
            if self.ipv4_pattern.fullmatch(raw_value.strip()):
                continue

            number = match.number
            if not phonenumbers.is_possible_number(number):
                continue
            is_valid = phonenumbers.is_valid_number(number)
            explicit_international_prefix = raw_value.lstrip().startswith(("+", "00"))
            if not is_valid and not explicit_international_prefix:
                # A region-less national-looking digit string is too
                # ambiguous to call a phone number. Keep the historical
                # Turkish default only when the library validates it.
                continue

            e164 = phonenumbers.format_number(number, PhoneNumberFormat.E164)
            region = phonenumbers.region_code_for_number(number) or phonenumbers.region_code_for_country_code(
                number.country_code
            )
            region = region or "UNKNOWN"
            # Keep the historical Turkish local representation for backward
            # compatibility while exposing E.164 for every international value.
            normalized = e164
            if region == "TR" and e164.startswith("+90"):
                normalized = f"0{e164[3:]}"
            validation_status = "VALID" if is_valid else "POSSIBLE"
            metadata = {
                "country_code": region,
                "calling_code": str(number.country_code),
                "normalized": normalized,
                "e164": e164,
                "validation_status": validation_status,
            }
            entities.append(
                DetectionCandidate(
                    "PHONE",
                    raw_value,
                    match.start,
                    match.end,
                    0.97 if validation_status == "VALID" else 0.90,
                    "phonenumbers",
                    metadata,
                )
            )
        return entities

    def _detect_emails(self, text: str) -> list[DetectionCandidate]:
        return [self._candidate("EMAIL", match, 0.96) for match in self.email_pattern.finditer(text)]

    def _detect_ibans(self, text: str) -> list[DetectionCandidate]:
        entities: list[DetectionCandidate] = []
        for match in self.iban_pattern.finditer(text):
            normalized = compact_identifier(match.group()).upper()
            if is_valid_turkish_iban(normalized):
                entities.append(self._candidate("IBAN", match, 0.99, {"normalized": normalized}))
        return entities

    def _detect_cards(self, text: str) -> list[DetectionCandidate]:
        return [
            self._candidate("CREDIT_CARD", match, 0.98, {"normalized": compact_identifier(match.group())})
            for match in self.card_pattern.finditer(text)
            if is_valid_luhn(match.group())
        ]

    def _detect_ips(self, text: str) -> list[DetectionCandidate]:
        return [
            self._candidate("IP_ADDRESS", match, 0.97)
            for match in self.ipv4_pattern.finditer(text)
            if is_valid_ipv4(match.group())
        ]

    def _detect_urls(self, text: str) -> list[DetectionCandidate]:
        entities: list[DetectionCandidate] = []
        for match in self.url_pattern.finditer(text):
            value = match.group().rstrip(".,;:!?)]}")
            if value:
                entities.append(
                    DetectionCandidate("URL", value, match.start(), match.start() + len(value), 0.90, "regex")
                )
        return entities

    def _detect_dates(self, text: str) -> list[DetectionCandidate]:
        return [
            self._candidate("DATE", match, 0.95)
            for match in self.date_pattern.finditer(text)
            if is_valid_date(match.group())
        ]

    def _detect_passports(self, text: str) -> list[DetectionCandidate]:
        entities: list[DetectionCandidate] = []
        for match in self.passport_pattern.finditer(text):
            value = match.group("value")
            compact = value.replace("-", "").upper()
            start, end = match.span("value")
            if not any(char.isdigit() for char in compact):
                # A keyword followed by a normal word (for example, "passport
                # context") is not an identifier.
                continue
            strict_format = bool(
                re.fullmatch(r"[A-Z]{1,2}\d{6,9}", compact)
                or re.fullmatch(r"\d{6,9}", compact)
            )
            entity_type = "PASSPORT_ID" if strict_format else "POSSIBLE_PASSPORT_ID"
            entities.append(
                DetectionCandidate(
                    entity_type,
                    value,
                    start,
                    end,
                    0.90 if strict_format else 0.45,
                    "regex",
                    {
                        "validation_status": "CONTEXTUAL_FORMAT"
                        if strict_format
                        else "UNKNOWN_FORMAT"
                    },
                )
            )
        return entities

    def _detect_suspicious_tc_ids(
        self,
        text: str,
        excluded_spans: list[tuple[int, int]] | None = None,
    ) -> list[DetectionCandidate]:
        excluded_spans = excluded_spans or []
        return [
            self._candidate(
                "POSSIBLE_TC_ID",
                match,
                0.42,
                {"validation_status": "INVALID_CHECKSUM"},
            )
            for match in self.tc_id_pattern.finditer(text)
            if not is_valid_tc_id(match.group())
            and not any(match.start() < end and start < match.end() for start, end in excluded_spans)
        ]

    def _detect_suspicious_ibans(self, text: str) -> list[DetectionCandidate]:
        entities: list[DetectionCandidate] = []
        for match in self.iban_pattern.finditer(text):
            normalized = compact_identifier(match.group()).upper()
            if not is_valid_turkish_iban(normalized):
                entities.append(
                    self._candidate(
                        "POSSIBLE_IBAN",
                        match,
                        0.45,
                        {
                            "normalized": normalized,
                            "validation_status": "INVALID_CHECKSUM",
                        },
                    )
                )
        return entities

    def _detect_suspicious_cards(
        self,
        text: str,
        excluded_spans: list[tuple[int, int]] | None = None,
    ) -> list[DetectionCandidate]:
        excluded_spans = excluded_spans or []
        return [
            self._candidate(
                "POSSIBLE_CREDIT_CARD",
                match,
                0.42,
                {
                    "normalized": compact_identifier(match.group()),
                    "validation_status": "INVALID_CHECKSUM",
                },
            )
            for match in self.card_pattern.finditer(text)
            if not is_valid_luhn(match.group())
            and not any(match.start() < end and start < match.end() for start, end in excluded_spans)
        ]

    @staticmethod
    def _candidate(
        entity_type: str,
        match: re.Match[str],
        confidence: float,
        metadata: dict[str, str] | None = None,
    ) -> DetectionCandidate:
        return DetectionCandidate(
            entity_type,
            match.group(),
            match.start(),
            match.end(),
            confidence,
            "regex",
            metadata or {},
        )
