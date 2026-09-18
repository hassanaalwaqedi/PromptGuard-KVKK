"""Prompt sanitization helpers and policy."""

from app.schemas.entities import DetectedEntity
from app.services.sanitization.policy import SANITIZATION_POLICY, SanitizationAction, action_for


def sanitize_prompt(prompt: str, entities: list[DetectedEntity]) -> str:
    """Lazily expose the implementation without importing risk models eagerly."""
    from app.services.sanitization.sanitizer import sanitize_prompt as _sanitize_prompt

    return _sanitize_prompt(prompt, entities)

__all__ = ["SANITIZATION_POLICY", "SanitizationAction", "action_for", "sanitize_prompt"]
