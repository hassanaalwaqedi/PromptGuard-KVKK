"""Offset-preserving, policy-aware prompt sanitization."""

from __future__ import annotations

from app.schemas.entities import DetectedEntity
from app.services.risk.weights import weight_for
from app.services.sanitization.policy import action_for


def sanitize_prompt(
    prompt: str,
    entities: list[DetectedEntity],
) -> str:
    """Apply centralized KEEP/PSEUDONYMIZE/MASK actions to resolved spans.

    The output is constructed left-to-right so every character outside a final
    entity span is copied exactly once. Person mappings exist only for this
    call, which keeps repeated names consistent without persistence.
    """
    spans = sorted(
        (entity for entity in entities if 0 <= entity.start < entity.end <= len(prompt)),
        # Prefer the more sensitive detector at a shared start, then the
        # longest span. This mirrors Phase 2 resolver specificity and avoids a
        # broad semantic span swallowing a precise financial/identity span.
        key=lambda entity: (entity.start, -weight_for(entity.type), -(entity.end - entity.start), entity.end),
    )

    selected: list[DetectedEntity] = []
    for entity in spans:
        if selected and entity.start < selected[-1].end:
            continue
        selected.append(entity)

    person_placeholders: dict[str, str] = {}
    output: list[str] = []
    cursor = 0
    for entity in selected:
        output.append(prompt[cursor : entity.start])
        action = action_for(entity.type)
        if action == "KEEP":
            replacement = entity.text
        elif action == "PSEUDONYMIZE":
            key = entity.text.casefold()
            if key not in person_placeholders:
                person_placeholders[key] = f"[PERSON_{len(person_placeholders) + 1}]"
            replacement = person_placeholders[key]
        elif action == "WARN":
            # Suspicious near-matches are surfaced honestly but left intact;
            # callers can review them without pretending validation succeeded.
            replacement = entity.text
        else:
            replacement = f"[{entity.type}]"
        output.append(replacement)
        cursor = entity.end
    output.append(prompt[cursor:])
    return "".join(output)
