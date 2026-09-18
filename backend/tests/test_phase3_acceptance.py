"""Acceptance coverage for the Phase 3 risk and privacy contract."""

from pathlib import Path
import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.entities import DetectedEntity
from app.services.risk import RiskEngine
from app.services.risk.policy import policy_for_level
from app.services.risk.weights import risk_level_for_score
from app.services.sanitization import sanitize_prompt


def _entity(entity_type: str, text: str, confidence: float = 0.99, start: int = 0) -> DetectedEntity:
    return DetectedEntity(
        type=entity_type,
        text=text,
        start=start,
        end=start + len(text),
        confidence=confidence,
        source="test",
    )


@pytest.mark.parametrize(
    ("prompt", "expected_types"),
    [
        ("Ara +90 532 123 45 67", ["PHONE"]),
        ("Sayi 12345678901", []),
        ("Email user@example.com", ["EMAIL"]),
        ("Hesap TR330006100519786457841326", ["IBAN"]),
        ("Hesap TR330006100519786457841327", []),
        ("Kart 4242-4242-4242-4242", ["CREDIT_CARD"]),
        ("Kart 4242-4242-4242-4241", []),
        ("Sunucu 192.168.1.1", ["IP_ADDRESS"]),
        ("Sunucu 999.999.999.999", []),
        ("Tarih 18/09/2026", ["DATE"]),
        ("Tarih 31/02/2026", []),
        ("Site https://example.com/path", ["URL"]),
        ("Kimlik 10000000146", ["TC_ID"]),
        ("Kimlik 12345678901", []),
        (
            "Ahmet Y\u0131lmaz, +90 532 123 45 67, user@example.com, TR330006100519786457841326",
            ["PERSON", "PHONE", "EMAIL", "IBAN"],
        ),
        ("Please email user@example.com hakk\u0131nda bilgi ver.", ["EMAIL"]),
        ("\u0130stanbul'da Ay\u015fe \u00d6zt\u00fcrk", ["LOCATION", "PERSON"]),
        ("Please summarize this public document.", []),
    ],
)
def test_post_analyze_acceptance_cases(prompt: str, expected_types: list[str]) -> None:
    with TestClient(app) as client:
        response = client.post("/api/v1/analyze", json={"prompt": prompt})

    assert response.status_code == 200
    body = response.json()
    entities = body["entities"]
    assert [entity["type"] for entity in entities] == expected_types
    assert len({(entity["type"], entity["start"], entity["end"]) for entity in entities}) == len(entities)
    for entity in entities:
        assert prompt[entity["start"] : entity["end"]] == entity["text"]
        assert entity["start"] < entity["end"]
    assert body["entity_count"] == len(entities)
    assert body["sanitized_prompt"]


def test_semantic_provider_is_reported_without_faking_bare_organization_detection() -> None:
    prompt = "Ahmet Y\u0131lmaz \u0130stanbul'da Microsoft i\u00e7in \u00e7al\u0131\u015f\u0131yor."
    with TestClient(app) as client:
        body = client.post("/api/v1/analyze", json={"prompt": prompt}).json()

    assert body["ner_provider"] == "heuristic-local"
    assert {entity["type"] for entity in body["entities"]} >= {"PERSON", "LOCATION"}
    assert "Microsoft" not in {entity["text"] for entity in body["entities"]}


def test_risk_boundaries_and_policy_are_inclusive() -> None:
    assert [risk_level_for_score(value) for value in (0, 20, 21, 45, 46, 70, 71, 100)] == [
        "LOW",
        "LOW",
        "MEDIUM",
        "MEDIUM",
        "HIGH",
        "HIGH",
        "CRITICAL",
        "CRITICAL",
    ]
    assert [policy_for_level(level) for level in ("LOW", "MEDIUM", "HIGH", "CRITICAL")] == [
        "ALLOW",
        "WARN",
        "MASK",
        "BLOCK",
    ]


def test_risk_engine_samples_and_bounded_repetition() -> None:
    engine = RiskEngine()
    safe = engine.evaluate([]).summary
    tc = engine.evaluate([_entity("TC_ID", "10000000146")]).summary
    tc_phone = engine.evaluate([_entity("TC_ID", "10000000146"), _entity("PHONE", "+905321234567", start=12)]).summary
    tc_iban_person = engine.evaluate(
        [_entity("TC_ID", "10000000146"), _entity("IBAN", "TR330006100519786457841326", start=12), _entity("PERSON", "Ahmet", start=40)]
    ).summary
    repeated = engine.evaluate([_entity("EMAIL", "user@example.com"), _entity("EMAIL", "user@example.com", start=20)]).summary

    assert (safe.score, safe.level, safe.decision) == (0, "LOW", "ALLOW")
    assert tc.level == "HIGH" and tc.decision == "MASK"
    assert tc_phone.level == "CRITICAL" and tc_phone.decision == "BLOCK" and tc_phone.score > tc.score
    assert tc_iban_person.level == "CRITICAL" and tc_iban_person.decision == "BLOCK"
    assert 0 <= repeated.score <= 100


def test_sanitizer_replaces_exact_spans_and_resolves_overlap() -> None:
    prompt = "ID 10000000146 and 10000000146"
    first = _entity("TC_ID", "10000000146", start=3)
    second_start = prompt.rindex("10000000146")
    second = _entity("TC_ID", "10000000146", start=second_start)
    overlapping = _entity("PERSON", "10000000146 and", start=3)
    assert sanitize_prompt(prompt, [first, second, overlapping]) == "ID [TC_ID] and [TC_ID]"

    unicode_prompt = "\u0130stanbul \u2014 user@example.com"
    location_start = 0
    email_start = unicode_prompt.index("user@example.com")
    assert sanitize_prompt(
        unicode_prompt,
        [_entity("LOCATION", "\u0130stanbul", start=location_start), _entity("EMAIL", "user@example.com", start=email_start)],
    ) == "\u0130stanbul \u2014 [EMAIL]"


def test_privacy_contract_has_no_prompt_or_entity_columns_and_no_persistence() -> None:
    db_path = Path(__file__).parents[1] / "promptguard.db"
    with TestClient(app) as client:
        response = client.post("/api/v1/analyze", json={"prompt": "user@example.com"})
    assert response.status_code == 200

    with sqlite3.connect(db_path) as connection:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(analyses)")}
        row_count = connection.execute("SELECT COUNT(*) FROM analyses").fetchone()[0]
    assert columns == {"id", "created_at", "status"}
    assert row_count == 0

    source_files = list((Path(__file__).parents[1] / "app").rglob("*.py"))
    source = "\n".join(path.read_text(encoding="utf-8") for path in source_files)
    assert "print(" not in source
    assert "logger." not in source
    assert '"Internal server error."' in source
