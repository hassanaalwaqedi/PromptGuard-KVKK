"""Lightweight local semantic detection with no external model dependency."""

import re

from app.services.detection.base import DetectionCandidate


class HeuristicNerDetector:
    """Conservative multilingual heuristics for common semantic entities.

    This provider intentionally uses only curated vocabulary and context-aware
    capitalization patterns. It is deterministic and does not download or
    initialize an ML model.
    """

    provider_name = "heuristic-local"
    available = True

    _capitalized_word = (
        r"[A-Z\u00c0-\u00d6\u00d8-\u00de\u00c7\u011e\u0130\u00d6\u015e\u00dc]"
        r"[a-z\u00df-\u00f6\u00f8-\u00ff\u00e7\u011f\u0131\u00f6\u015f\u00fc]+"
        r"(?:[-'][A-Z\u00c0-\u00d6\u00d8-\u00de\u00c7\u011e\u0130\u00d6\u015e\u00dc]"
        r"[a-z\u00df-\u00f6\u00f8-\u00ff\u00e7\u011f\u0131\u00f6\u015f\u00fc]+)*"
    )
    _first_names = (
        "Ahmet|Ay\u015fe|Mehmet|Fatma|Ali|Zeynep|Mustafa|Elif|Emre|Merve|Can|"
        "Deniz|Hakan|Selin|Hasan|Aylin|John|Jane|Michael|Sarah|Daniel|Jessica|"
        "David|Robert|Emily|William|James|Olivia|Sophia|Emma|Liam|Anne-Marie|"
        "Andrew|Christopher|Jennifer|Matthew|Thomas|Elizabeth|Alexander|"
        "Alexander|Mia|Charlotte|Sophie|George|Henry|Grace|Ethan"
    )
    person_pattern = re.compile(
        rf"(?<!\w)(?i:(?:{_first_names}))\s+{_capitalized_word}(?!\w)",
        re.UNICODE,
    )
    context_person_pattern = re.compile(
        rf"(?<!\w)"
        rf"(?:(?i:(?:customer|client|user)\s+(?:is|named|called)\s+)"
        rf"|(?i:(?:employee|contact|person|manager|colleague|patient|applicant)\s+)"
        rf"|(?i:(?:mr|mrs|ms|miss|dr))\.?\s+)"
        rf"(?P<name>{_capitalized_word}\s+{_capitalized_word})(?!\w)",
        re.UNICODE,
    )

    _locations = (
        "San Francisco",
        "New York",
        "United Kingdom",
        "Saudi Arabia",
        "Istanbul",
        "\u0130stanbul",
        "Ankara",
        "Antalya",
        "Bursa",
        "London",
        "Berlin",
        "Paris",
        "Rome",
        "Dubai",
        "Riyadh",
        "Jeddah",
        "Adana",
        "Eski\u015fehir",
        "Izmir",
        "\u0130zmir",
        "Kad\u0131k\u00f6y",
        "Konya",
        "\u00dcrkiye",
        "T\u00dcRK\u0130YE",
        "TURKIYE",
        "Turkey",
        "Germany",
        "France",
        "Italy",
        "United States",
        "United Arab Emirates",
        "Saudi Arabia",
    )
    location_pattern = re.compile(
        rf"(?<!\w)(?:{'|'.join(re.escape(location) for location in sorted(set(_locations), key=len, reverse=True))})(?!\w)",
        re.IGNORECASE | re.UNICODE,
    )

    _known_organizations = (
        "Microsoft",
        "OpenAI",
        "Google",
        "Apple",
        "Northstar Systems",
        "Example Teknoloji",
        "Example University",
        "Example Bank",
        "Example Hospital",
    )
    organization_pattern = re.compile(
        rf"(?<!\w)(?:{'|'.join(re.escape(name) for name in sorted(_known_organizations, key=len, reverse=True))})(?!\w)",
        re.IGNORECASE | re.UNICODE,
    )
    _organization_suffix = (
        r"(?:A\.?\s*(?:\u015e|S)\.?|A\u015e|AS|Ltd\.?|Limited|Inc\.?|LLC|GmbH|"
        r"Corp\.?|Corporation|Company|Systems|Technologies|Technology|Bank|"
        r"University|Hospital|Group|Holdings|\u015eirketi|\u00dcniversitesi|"
        r"Bankas\u0131|Belediyesi)"
    )
    organization_suffix_pattern = re.compile(
        rf"(?<!\w)(?P<name>(?:[A-Za-z\u00c0-\u00ff\u00c7\u011e\u0130\u015e\u00dc][\w'&.-]*\s+){{0,3}}"
        rf"{_organization_suffix})(?!\w)",
        re.IGNORECASE | re.UNICODE,
    )
    _organization_prefix_stopwords = {
        "a",
        "an",
        "and",
        "at",
        "by",
        "company",
        "employed",
        "for",
        "from",
        "in",
        "is",
        "of",
        "the",
        "with",
        "works",
    }

    @classmethod
    def _is_prefix_stopword(cls, value: str) -> bool:
        token = value.casefold().rstrip(".,")
        if token in cls._organization_prefix_stopwords:
            return True
        # Turkish locative/possessive forms such as "Ankara'da" are context
        # around an organization, not part of its name.
        if "'" in token:
            suffix = token.rsplit("'", 1)[-1]
            return suffix in {"da", "de", "ta", "te", "a", "e", "i", "ı", "u", "ü"}
        return False

    def detect(self, text: str) -> list[DetectionCandidate]:
        entities: list[DetectionCandidate] = []
        entities.extend(self._candidates("ORGANIZATION", self.organization_pattern, text, 0.86))
        entities.extend(self._organization_suffix_candidates(text))
        entities.extend(self._candidates("LOCATION", self.location_pattern, text, 0.84))
        entities.extend(self._candidates("PERSON", self.person_pattern, text, 0.80))
        entities.extend(self._group_candidates("PERSON", self.context_person_pattern, text, 0.88, "name"))
        return entities

    def _organization_suffix_candidates(self, text: str) -> list[DetectionCandidate]:
        entities: list[DetectionCandidate] = []
        for match in self.organization_suffix_pattern.finditer(text):
            raw_value = match.group("name")
            words = raw_value.split()
            drop_count = 0
            connectors = {"and", "at", "by", "for", "from", "with"}
            for index, word in enumerate(words[:-1]):
                if word.casefold().rstrip(".,") in connectors:
                    drop_count = index + 1
            if drop_count == 0:
                while len(words) > 1 and self._is_prefix_stopword(words[0]):
                    words.pop(0)
                    drop_count += 1
            start = match.start("name")
            if drop_count:
                first_kept_word = raw_value.split()[drop_count]
                start += raw_value.find(first_kept_word)
            end = match.end("name")
            if value := text[start:end]:
                # Sentence punctuation after abbreviated legal suffixes is not
                # part of the organization span (A.Ş. is kept intact).
                if value.endswith(".") and not re.search(r"A\.\s*[ŞS]\.$", value, re.IGNORECASE):
                    end -= 1
            value = text[start:end]
            entities.append(
                DetectionCandidate(
                    "ORGANIZATION",
                    text[start:end],
                    start,
                    end,
                    0.84,
                    "ner",
                    {"provider": self.provider_name},
                )
            )
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

    def _group_candidates(
        self,
        entity_type: str,
        pattern: re.Pattern[str],
        text: str,
        confidence: float,
        group: str,
    ) -> list[DetectionCandidate]:
        return [
            DetectionCandidate(
                entity_type,
                match.group(group),
                match.start(group),
                match.end(group),
                confidence,
                "ner",
                {"provider": self.provider_name},
            )
            for match in pattern.finditer(text)
        ]
