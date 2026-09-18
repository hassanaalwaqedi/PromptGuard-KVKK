"""Lightweight local semantic detector with no external model dependency."""

import re

from app.services.detection.base import DetectionCandidate


class HeuristicNerDetector:
    """A conservative local fallback for common Turkish prompt examples.

    It favors precision over recall. A future model-backed provider can implement
    the same interface without changing the DetectionService.
    """

    provider_name = "heuristic-local"
    available = True

    _capitalized_word = r"[A-Z\u00c7\u011e\u0130\u00d6\u015e\u00dc][a-z\u00e7\u011f\u0131\u00f6\u015f\u00fc]+"
    _first_names = (
        "Ahmet|Ay\u015fe|Mehmet|Fatma|Ali|Zeynep|Mustafa|Elif|Emre|Merve|Can|"
        "Deniz|Hakan|Selin|Hasan|Aylin|John|Jane|Michael|Sarah"
    )
    person_pattern = re.compile(
        rf"\b(?:{_first_names})\s+{_capitalized_word}\b",
        re.UNICODE,
    )
    organization_pattern = re.compile(
        rf"\b{_capitalized_word}(?:\s+{_capitalized_word}){{0,3}}\s+"
        r"(?:A\.?\s*\u015e\.?|A\u015e|Ltd\.?\s*(?:\u015eti\.?)?|\u015eirketi|\u00dcniversitesi|Bankas\u0131|Belediyesi)(?=\s|$|[,.;:])",
        re.UNICODE,
    )
    location_pattern = re.compile(
        r"\b(?:Adana|Ankara|Antalya|Bursa|Eski\u015fehir|Istanbul|\u0130stanbul|Izmir|\u0130zmir|"
        r"Kad\u0131k\u00f6y|Konya|T\u00fcrkiye|Turkey)\b",
        re.UNICODE,
    )

    def detect(self, text: str) -> list[DetectionCandidate]:
        entities: list[DetectionCandidate] = []
        entities.extend(self._candidates("ORGANIZATION", self.organization_pattern, text, 0.82))
        entities.extend(self._candidates("LOCATION", self.location_pattern, text, 0.80))
        entities.extend(self._candidates("PERSON", self.person_pattern, text, 0.76))
        return entities

    def _candidates(
        self,
        entity_type: str,
        pattern: re.Pattern[str],
        text: str,
        confidence: float,
    ) -> list[DetectionCandidate]:
        return [
            DetectionCandidate(
                entity_type,
                match.group(),
                match.start(),
                match.end(),
                confidence,
                "ner",
                {"provider": self.provider_name},
            )
            for match in pattern.finditer(text)
        ]
