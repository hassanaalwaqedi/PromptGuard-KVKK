"""Focused acceptance tests for the policy-aware sanitizer."""

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.entities import DetectedEntity
from app.services.sanitization import SANITIZATION_POLICY, action_for, sanitize_prompt


def _entity(entity_type: str, text: str, start: int) -> DetectedEntity:
    return DetectedEntity(
        type=entity_type,
        text=text,
        start=start,
        end=start + len(text),
        confidence=0.99,
        source="test",
    )


def _spans(prompt: str, values: list[tuple[str, str]]) -> list[DetectedEntity]:
    seen: dict[str, int] = {}
    result: list[DetectedEntity] = []
    for entity_type, value in values:
        start = prompt.index(value, seen.get(value, 0))
        seen[value] = start + len(value)
        result.append(_entity(entity_type, value, start))
    return result


def test_centralized_default_policy_is_explicit() -> None:
    assert SANITIZATION_POLICY == {
        "TC_ID": "MASK",
        "PASSPORT_ID": "MASK",
        "CREDIT_CARD": "MASK",
        "IBAN": "MASK",
        "PHONE": "MASK",
        "EMAIL": "MASK",
        "IP_ADDRESS": "MASK",
        "PERSON": "PSEUDONYMIZE",
        "LOCATION": "KEEP",
        "ORGANIZATION": "KEEP",
        "DATE": "KEEP",
        "URL": "KEEP",
    }
    assert action_for("future_type") == "KEEP"


def test_person_pseudonyms_are_consistent_and_distinct() -> None:
    prompt = (
        "Ahmet Y\u0131lmaz \u0130stanbul'da ya\u015f\u0131yor.\n"
        "Ahmet Y\u0131lmaz Mehmet Demir'i arad\u0131.\n"
        "Mehmet Demir'in telefonu +90 532 123 45 67."
    )
    entities = _spans(
        prompt,
        [
            ("PERSON", "Ahmet Y\u0131lmaz"),
            ("LOCATION", "\u0130stanbul"),
            ("PERSON", "Ahmet Y\u0131lmaz"),
            ("PERSON", "Mehmet Demir"),
            ("PERSON", "Mehmet Demir"),
            ("PHONE", "+90 532 123 45 67"),
        ],
    )
    assert sanitize_prompt(prompt, entities) == (
        "[PERSON_1] \u0130stanbul'da ya\u015f\u0131yor.\n"
        "[PERSON_1] [PERSON_2]'i arad\u0131.\n"
        "[PERSON_2]'in telefonu [PHONE]."
    )


def test_keep_entities_preserve_text_and_mask_entities_never_expose_values() -> None:
    prompt = (
        "\u0130stanbul Microsoft 18/09/2026 https://example.com/account | "
        "10000000146 TR330006100519786457841326 4242-4242-4242-4242 "
        "+90 532 123 45 67 test@example.com 192.168.1.1"
    )
    values = [
        ("LOCATION", "\u0130stanbul"),
        ("ORGANIZATION", "Microsoft"),
        ("DATE", "18/09/2026"),
        ("URL", "https://example.com/account"),
        ("TC_ID", "10000000146"),
        ("IBAN", "TR330006100519786457841326"),
        ("CREDIT_CARD", "4242-4242-4242-4242"),
        ("PHONE", "+90 532 123 45 67"),
        ("EMAIL", "test@example.com"),
        ("IP_ADDRESS", "192.168.1.1"),
    ]
    sanitized = sanitize_prompt(prompt, _spans(prompt, values))
    assert sanitized.startswith("\u0130stanbul Microsoft 18/09/2026 https://example.com/account | ")
    assert sanitized.endswith("[TC_ID] [IBAN] [CREDIT_CARD] [PHONE] [EMAIL] [IP_ADDRESS]")
    for _, value in values[4:]:
        assert value not in sanitized
    for _, value in values[:4]:
        assert value in sanitized


def test_offsets_preserve_adjacent_punctuation_multiline_start_and_end() -> None:
    prompt = "Ahmet\u0130stanbul,\nuser@example.com"
    entities = [
        _entity("PERSON", "Ahmet", 0),
        _entity("LOCATION", "\u0130stanbul", 5),
        _entity("EMAIL", "user@example.com", prompt.index("user@example.com")),
    ]
    assert sanitize_prompt(prompt, entities) == "[PERSON_1]\u0130stanbul,\n[EMAIL]"

    end_prompt = "Phone: +90 532 123 45 67"
    phone_start = end_prompt.index("+90")
    assert sanitize_prompt(end_prompt, [_entity("PHONE", "+90 532 123 45 67", phone_start)]) == "Phone: [PHONE]"


def test_api_returns_actions_and_keeps_context_without_changing_risk() -> None:
    prompt = "Ahmet Y\u0131lmaz \u0130stanbul'da 18/09/2026, phone +90 532 123 45 67"
    with TestClient(app) as client:
        body = client.post("/api/v1/analyze", json={"prompt": prompt}).json()

    by_type = {entity["type"]: entity for entity in body["entities"]}
    assert by_type["PERSON"]["sanitization_action"] == "PSEUDONYMIZE"
    assert by_type["LOCATION"]["sanitization_action"] == "KEEP"
    assert by_type["DATE"]["sanitization_action"] == "KEEP"
    assert by_type["PHONE"]["sanitization_action"] == "MASK"
    assert "[PERSON_1] \u0130stanbul'da 18/09/2026, phone [PHONE]" == body["sanitized_prompt"]
    assert body["risk"]["score"] > 0
    assert by_type["LOCATION"]["risk_contribution"] > 0
    assert by_type["DATE"]["risk_contribution"] > 0


def test_pseudonymization_is_transient_and_not_written_to_source_or_database() -> None:
    source = "\n".join(path.read_text(encoding="utf-8") for path in (Path(__file__).parents[1] / "app").rglob("*.py"))
    assert "person_placeholders" in source
    assert "INSERT INTO" not in source
    assert "print(" not in source
