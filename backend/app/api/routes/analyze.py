"""Phase 3 in-memory detection, risk, and sanitization route."""

from uuid import uuid4

from fastapi import APIRouter

from app.schemas.analysis import AnalyzeRequest, AnalyzeResponse
from app.services.detection import DetectionService
from app.services.risk import RiskEngine
from app.services.sanitization import action_for, sanitize_prompt

router = APIRouter(tags=["analysis"])
detection_service = DetectionService()
risk_engine = RiskEngine()


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_prompt(request: AnalyzeRequest) -> AnalyzeResponse:
    """Detect entities transiently without logging or persisting prompt content."""
    entities = detection_service.detect(request.prompt)
    assessment = risk_engine.evaluate(entities)
    response_entities = [
        entity.model_copy(update={"sanitization_action": action_for(entity.type)})
        for entity in assessment.entities
    ]
    return AnalyzeResponse(
        analysis_id=uuid4(),
        entity_count=len(entities),
        entities=response_entities,
        status="analyzed",
        ner_available=detection_service.ner_available,
        ner_provider=detection_service.ner_provider,
        risk=assessment.summary,
        risk_factors=assessment.factors,
        sanitized_prompt=sanitize_prompt(request.prompt, entities),
    )
