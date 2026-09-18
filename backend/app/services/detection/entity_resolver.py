"""Deduplication and overlap resolution for detection candidates."""

from app.services.detection.base import DetectionCandidate


class EntityResolver:
    """Keep the most specific, highest-confidence entity for each overlap."""

    _specificity = {
        "IBAN": 100,
        "TC_ID": 99,
        "CREDIT_CARD": 98,
        "EMAIL": 95,
        "PHONE": 94,
        "URL": 90,
        "IP_ADDRESS": 89,
        "PASSPORT_ID": 88,
        "DATE": 80,
        "ORGANIZATION": 70,
        "PERSON": 60,
        "LOCATION": 50,
    }

    def resolve(self, candidates: list[DetectionCandidate]) -> list[DetectionCandidate]:
        ranked = sorted(
            candidates,
            key=lambda entity: (
                -self._specificity.get(entity.type, 0),
                -entity.confidence,
                -(entity.end - entity.start),
                entity.start,
            ),
        )
        selected: list[DetectionCandidate] = []
        for candidate in ranked:
            if not any(self._overlaps(candidate, accepted) for accepted in selected):
                selected.append(candidate)
        return sorted(selected, key=lambda entity: (entity.start, entity.end, entity.type))

    @staticmethod
    def _overlaps(left: DetectionCandidate, right: DetectionCandidate) -> bool:
        return left.start < right.end and right.start < left.end
