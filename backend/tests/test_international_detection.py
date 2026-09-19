from __future__ import annotations

from time import perf_counter

from fastapi.testclient import TestClient

from app.main import app
from app.services.detection.detection_service import DetectionService


def test_international_phone_formats_keep_exact_offsets_and_metadata() -> None:
    prompt = "+90 532 123 45 67 | +44 7700 900123 | +49 151 23456789 | +1 415 555 2671 | +966 50 123 4567"
    entities = [entity for entity in DetectionService().detect(prompt) if entity.type == "PHONE"]

    assert [entity.text for entity in entities] == [
        "+90 532 123 45 67",
        "+44 7700 900123",
        "+49 151 23456789",
        "+1 415 555 2671",
        "+966 50 123 4567",
    ]
    assert [entity.metadata["country_code"] for entity in entities] == ["TR", "GB", "DE", "US", "SA"]
    assert entities[1].metadata["normalized"] == "+447700900123"
    assert all(prompt[entity.start : entity.end] == entity.text for entity in entities)


def test_english_names_are_contextual_and_common_false_positives_stay_hidden() -> None:
    prompt = (
        "customer is Daniel Carter; her manager David Miller; another person Jessica Moore; "
        "employee Sarah Collins. Customer Risk Report. Privacy Firewall. Northstar Systems."
    )
    entities = DetectionService().detect(prompt)
    people = [entity.text for entity in entities if entity.type == "PERSON"]
    organizations = [entity.text for entity in entities if entity.type == "ORGANIZATION"]

    assert people == ["Daniel Carter", "David Miller", "Jessica Moore", "Sarah Collins"]
    assert organizations == ["Northstar Systems"]


def test_locations_and_organizations_are_case_insensitive_and_offset_safe() -> None:
    prompt = "Berlin London Istanbul Riyadh Dubai Saudi Arabia Germany; works for Microsoft and Contoso Ltd."
    entities = DetectionService().detect(prompt)
    locations = [entity for entity in entities if entity.type == "LOCATION"]
    organizations = [entity for entity in entities if entity.type == "ORGANIZATION"]

    assert [entity.text for entity in locations] == ["Berlin", "London", "Istanbul", "Riyadh", "Dubai", "Saudi Arabia", "Germany"]
    assert [entity.text for entity in organizations] == ["Microsoft", "Contoso Ltd"]
    assert all(prompt[entity.start : entity.end] == entity.text for entity in entities)


def test_passports_require_context_and_support_numeric_values() -> None:
    prompt = "passport number U8473921; passport no 123456789; pasaport no U1234567; U8473921 alone"
    entities = DetectionService().detect(prompt)

    assert [(entity.type, entity.text) for entity in entities if "PASSPORT" in entity.type] == [
        ("PASSPORT_ID", "U8473921"),
        ("PASSPORT_ID", "123456789"),
        ("PASSPORT_ID", "U1234567"),
    ]


def test_suspicious_identifiers_are_unverified_warnings_not_validated_entities() -> None:
    prompt = "TR330006100519786457841327 | 4242 4242 4242 4241 | 12345678901"
    with TestClient(app) as client:
        body = client.post("/api/v1/analyze", json={"prompt": prompt}).json()

    assert [entity["type"] for entity in body["entities"]] == [
        "POSSIBLE_IBAN",
        "POSSIBLE_CREDIT_CARD",
        "POSSIBLE_TC_ID",
    ]
    assert all(entity["sanitization_action"] == "WARN" for entity in body["entities"])
    assert body["risk"]["decision"] == "WARN"
    assert body["sanitized_prompt"] == prompt


def test_messy_english_acceptance_prompt_detects_expected_entities_without_invalid_values() -> None:
    prompt = """hey can u clean this up and make a quick note for the team

customer is Daniel Carter i think he's in berlin now, works with northstar systems maybe
his mobile +49 151 23456789 and email daniel.carter@example.com

some account stuff he sent:
TR330006100519786457841326
card 4242 4242 4242 4242

btw passport was U8473921
and there was another person Jessica Moore involved, her number is +44 7700 900123

Daniel said send everything to jessica.moore@example.com

office server 192.168.20.15 and meeting should be 03/10/2026

not sure if these are real:
999.999.44.333
TR330006100519786457841327
4242 4242 4242 4241
31/02/2026
12345678901

oh and Sarah Collins from London mentioned the customer yesterday but idk if she is part of this"""
    entities = DetectionService().detect(prompt)
    values = {(entity.type, entity.text) for entity in entities}

    expected = {
        ("PERSON", "Daniel Carter"),
        ("PERSON", "Jessica Moore"),
        ("PERSON", "Sarah Collins"),
        ("LOCATION", "berlin"),
        ("LOCATION", "London"),
        ("ORGANIZATION", "northstar systems"),
        ("PHONE", "+49 151 23456789"),
        ("PHONE", "+44 7700 900123"),
        ("EMAIL", "daniel.carter@example.com"),
        ("EMAIL", "jessica.moore@example.com"),
        ("IBAN", "TR330006100519786457841326"),
        ("CREDIT_CARD", "4242 4242 4242 4242"),
        ("PASSPORT_ID", "U8473921"),
        ("IP_ADDRESS", "192.168.20.15"),
        ("DATE", "03/10/2026"),
        ("POSSIBLE_IBAN", "TR330006100519786457841327"),
        ("POSSIBLE_CREDIT_CARD", "4242 4242 4242 4241"),
        ("POSSIBLE_TC_ID", "12345678901"),
    }
    assert expected <= values
    assert ("IP_ADDRESS", "999.999.44.333") not in values
    assert ("DATE", "31/02/2026") not in values
    assert len({(entity.type, entity.start, entity.end) for entity in entities}) == len(entities)
    assert all(prompt[entity.start : entity.end] == entity.text for entity in entities)


def test_detection_stays_lightweight_and_does_not_initialize_a_model() -> None:
    service = DetectionService()
    prompt = "Contact Daniel Carter at daniel@example.com in London on 03/10/2026."
    started = perf_counter()
    for _ in range(25):
        service.detect(prompt)
    average_seconds = (perf_counter() - started) / 25

    assert service.ner_provider == "heuristic-local"
    assert average_seconds < 0.05
