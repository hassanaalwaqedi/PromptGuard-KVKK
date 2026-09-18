"""Orchestrator for the Phase 2 in-memory detection pipeline."""

from app.schemas.entities import DetectedEntity
from app.services.detection.entity_resolver import EntityResolver
from app.services.detection.ner_detector import HeuristicNerDetector
from app.services.detection.regex_detector import RegexDetector


class DetectionService:
    """Run normalization-aware detectors and return normalized entities."""

    def __init__(
        self,
        regex_detector: RegexDetector | None = None,
        ner_detector: HeuristicNerDetector | None = None,
        resolver: EntityResolver | None = None,
    ) -> None:
        self._regex_detector = regex_detector or RegexDetector()
        self._ner_detector = ner_detector or HeuristicNerDetector()
        self._resolver = resolver or EntityResolver()
        self._ner_runtime_available = self._ner_detector.available

    @property
    def ner_available(self) -> bool:
        return self._ner_runtime_available

    @property
    def ner_provider(self) -> str:
        return self._ner_detector.provider_name

    def detect(self, text: str) -> list[DetectedEntity]:
        """Detect in memory only; neither the prompt nor entity text is persisted."""
        candidates = self._regex_detector.detect(text)
        if self.ner_available:
            try:
                candidates.extend(self._ner_detector.detect(text))
            except Exception:
                # NER is an optional layer: no prompt content is logged on failure.
                self._ner_runtime_available = False
        return [
            DetectedEntity(
                type=candidate.type,
                text=candidate.text,
                start=candidate.start,
                end=candidate.end,
                confidence=candidate.confidence,
                source=candidate.source,
                metadata=candidate.metadata,
            )
            for candidate in self._resolver.resolve(candidates)
        ]
