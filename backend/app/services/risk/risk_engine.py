"""Explainable deterministic risk evaluation over Phase 2 entities."""

from __future__ import annotations

from collections import Counter
from math import floor

from app.schemas.entities import DetectedEntity
from app.schemas.risk import RiskAssessment, RiskEntity, RiskFactor, RiskSummary
from app.services.risk.explanations import reason_for
from app.services.risk.policy import policy_for_level
from app.services.risk.weights import (
    DIRECT_IDENTIFIER_CONTACT_BONUS,
    DIRECT_IDENTIFIER_EXPOSURE_BONUS,
    DIRECT_IDENTIFIER_FINANCIAL_BONUS,
    FINANCIAL_CONTACT_BONUS,
    MAX_RISK_SCORE,
    REPEATED_ENTITY_BONUS,
    SUSPICIOUS_IDENTIFIER_REVIEW_BONUS,
    THREE_CATEGORY_DIVERSITY_BONUS,
    category_for,
    risk_level_for_score,
    weight_for,
)


class RiskEngine:
    """Calculate bounded risk scores without persistence or external models."""

    def evaluate(self, entities: list[DetectedEntity]) -> RiskAssessment:
        risk_entities: list[RiskEntity] = []
        factors: list[RiskFactor] = []
        base_score = 0.0

        for entity in entities:
            weight = weight_for(entity.type)
            contribution = round(weight * entity.confidence, 2)
            base_score += contribution
            risk_entities.append(
                RiskEntity(
                    **entity.model_dump(),
                    category=category_for(entity.type),
                    base_weight=weight,
                    risk_contribution=contribution,
                    reason=reason_for(entity.type),
                )
            )
            if weight:
                factors.append(
                    RiskFactor(
                        kind="entity",
                        rule=f"ENTITY_WEIGHT:{entity.type}",
                        message=reason_for(entity.type),
                        bonus=contribution,
                        entity_type=entity.type,
                    )
                )

        types = {entity.type for entity in entities}
        categories = {category_for(entity.type) for entity in entities}
        meaningful_categories = categories - {"OTHER", "SUSPICIOUS_IDENTIFIER"}
        bonus = 0.0

        if types & {"TC_ID", "PASSPORT_ID"}:
            bonus += DIRECT_IDENTIFIER_EXPOSURE_BONUS
            factors.append(
                RiskFactor(
                    kind="sensitivity",
                    rule="DIRECT_IDENTIFIER_EXPOSURE",
                    message="A direct identity identifier increases exposure sensitivity.",
                    bonus=DIRECT_IDENTIFIER_EXPOSURE_BONUS,
                )
            )
        if "DIRECT_IDENTIFIER" in categories and "CONTACT_INFORMATION" in categories:
            bonus += DIRECT_IDENTIFIER_CONTACT_BONUS
            factors.append(
                RiskFactor(
                    kind="combination",
                    rule="DIRECT_IDENTIFIER_PLUS_CONTACT",
                    message="Direct identity and contact data occur together.",
                    bonus=DIRECT_IDENTIFIER_CONTACT_BONUS,
                )
            )
        if "DIRECT_IDENTIFIER" in categories and "FINANCIAL_INFORMATION" in categories:
            bonus += DIRECT_IDENTIFIER_FINANCIAL_BONUS
            factors.append(
                RiskFactor(
                    kind="combination",
                    rule="DIRECT_IDENTIFIER_PLUS_FINANCIAL",
                    message="Direct identity and financial data occur together.",
                    bonus=DIRECT_IDENTIFIER_FINANCIAL_BONUS,
                )
            )
        if {"FINANCIAL_INFORMATION", "CONTACT_INFORMATION"}.issubset(categories):
            bonus += FINANCIAL_CONTACT_BONUS
            factors.append(
                RiskFactor(
                    kind="combination",
                    rule="FINANCIAL_PLUS_CONTACT",
                    message="Financial and contact data occur together.",
                    bonus=FINANCIAL_CONTACT_BONUS,
                )
            )
        if len(meaningful_categories) >= 3:
            bonus += THREE_CATEGORY_DIVERSITY_BONUS
            factors.append(
                RiskFactor(
                    kind="combination",
                    rule="THREE_MEANINGFUL_CATEGORIES",
                    message="Three or more meaningful sensitivity categories occur together.",
                    bonus=THREE_CATEGORY_DIVERSITY_BONUS,
                )
            )

        if types & {
            "POSSIBLE_TC_ID",
            "POSSIBLE_PASSPORT_ID",
            "POSSIBLE_CREDIT_CARD",
            "POSSIBLE_IBAN",
        }:
            bonus += SUSPICIOUS_IDENTIFIER_REVIEW_BONUS
            factors.append(
                RiskFactor(
                    kind="sensitivity",
                    rule="SUSPICIOUS_IDENTIFIER_REVIEW",
                    message="An unverified identifier-like value requires review.",
                    bonus=SUSPICIOUS_IDENTIFIER_REVIEW_BONUS,
                )
            )

        repeated = Counter((entity.type, entity.text) for entity in entities)
        repeated_count = sum(1 for count in repeated.values() if count > 1)
        if repeated_count:
            repetition_bonus = repeated_count * REPEATED_ENTITY_BONUS
            bonus += repetition_bonus
            factors.append(
                RiskFactor(
                    kind="repetition",
                    rule="REPEATED_ENTITY",
                    message="Repeated detected entities add a bounded exposure factor.",
                    bonus=repetition_bonus,
                )
            )

        raw_score = base_score + bonus
        score = min(MAX_RISK_SCORE, max(0, floor(raw_score + 0.5)))
        level = risk_level_for_score(score)
        summary = RiskSummary(score=score, level=level, decision=policy_for_level(level))
        return RiskAssessment(entities=risk_entities, summary=summary, factors=factors)
