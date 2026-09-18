"""Deterministic regex detectors backed by identifier validators."""

import re

from app.services.detection.base import DetectionCandidate
from app.services.detection.normalization import compact_identifier, normalize_phone
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
    phone_pattern = re.compile(
        r"(?<![\w+])(?:(?:\+90|0090|0)[\s-]*)?\(?5\d{2}\)?[\s-]*\d{3}[\s-]*\d{2}[\s-]*\d{2}(?!\w)"
    )
    email_pattern = re.compile(r"(?<![\w.+-])[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}(?![\w-])", re.IGNORECASE)
    iban_pattern = re.compile(r"(?<![A-Z0-9])TR(?:[\s-]*\d){24}(?![A-Z0-9])", re.IGNORECASE)
    card_pattern = re.compile(r"(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)")
    ipv4_pattern = re.compile(r"(?<!\d)(?:\d{1,3}\.){3}\d{1,3}(?!\d)")
    url_pattern = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)
    date_pattern = re.compile(r"(?<!\d)(?:\d{1,2}[./]\d{1,2}[./]\d{4}|\d{4}-\d{1,2}-\d{1,2})(?!\d)")
    passport_pattern = re.compile(
        r"\b(?:passport|pasaport)(?:\s*(?:no|number|numarası))?\s*[:#-]?\s*([A-Z]{1,2}\d{6,8})\b",
        re.IGNORECASE,
    )

    def detect(self, text: str) -> list[DetectionCandidate]:
        entities: list[DetectionCandidate] = []
        entities.extend(self._detect_tc_ids(text))
        entities.extend(self._detect_phones(text))
        entities.extend(self._detect_emails(text))
        entities.extend(self._detect_ibans(text))
        entities.extend(self._detect_cards(text))
        entities.extend(self._detect_ips(text))
        entities.extend(self._detect_urls(text))
        entities.extend(self._detect_dates(text))
        entities.extend(self._detect_passports(text))
        return entities

    def _detect_tc_ids(self, text: str) -> list[DetectionCandidate]:
        return [
            self._candidate("TC_ID", match, 0.99)
            for match in self.tc_id_pattern.finditer(text)
            if is_valid_tc_id(match.group())
        ]

    def _detect_phones(self, text: str) -> list[DetectionCandidate]:
        entities: list[DetectionCandidate] = []
        for match in self.phone_pattern.finditer(text):
            normalized = normalize_phone(match.group())
            if normalized:
                entities.append(self._candidate("PHONE", match, 0.97, {"normalized": normalized}))
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
            start, end = match.span(1)
            entities.append(DetectionCandidate("PASSPORT_ID", match.group(1), start, end, 0.90, "regex"))
        return entities

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
