from app.services.detection.base import DetectionCandidate
from app.services.detection.detection_service import DetectionService
from app.services.detection.entity_resolver import EntityResolver
from app.services.detection.masking import mask_entity
from app.services.detection.regex_detector import RegexDetector
from app.services.detection.validators import (
    is_valid_date,
    is_valid_ipv4,
    is_valid_luhn,
    is_valid_tc_id,
    is_valid_turkish_iban,
)


def detected_types(text: str) -> list[str]:
    return [entity.type for entity in RegexDetector().detect(text)]


def test_tc_validator_accepts_synthetic_checksum_example_and_rejects_near_matches() -> None:
    assert is_valid_tc_id("10000000146")
    assert not is_valid_tc_id("10000000145")
    assert not is_valid_tc_id("00000000146")
    assert not is_valid_tc_id("12345678901")
    assert not is_valid_tc_id("11111111110")


def test_tc_detector_only_returns_checksum_valid_identifier() -> None:
    entities = RegexDetector().detect("Geçerli 10000000146, geçersiz 12345678901.")
    assert [(entity.type, entity.text) for entity in entities] == [("TC_ID", "10000000146")]


def test_turkish_phone_formats_and_normalized_metadata() -> None:
    entities = RegexDetector().detect("+90 532 123 45 67, 0532-123-45-67 ve 532 123 45 67")
    phones = [entity for entity in entities if entity.type == "PHONE"]
    assert len(phones) == 3
    assert {entity.metadata["normalized"] for entity in phones} == {"05321234567"}


def test_email_detection_has_exact_offsets() -> None:
    text = "Write to name.surname@company.com.tr today."
    entity = next(entity for entity in RegexDetector().detect(text) if entity.type == "EMAIL")
    assert entity.text == "name.surname@company.com.tr"
    assert text[entity.start : entity.end] == entity.text


def test_email_detection_allows_sentence_punctuation_after_address() -> None:
    text = "Email user@example.com."
    entities = [entity for entity in RegexDetector().detect(text) if entity.type == "EMAIL"]
    assert [(entity.text, entity.start, entity.end) for entity in entities] == [("user@example.com", 6, 22)]


def test_iban_validator_and_detector_accept_compact_and_spaced_example() -> None:
    compact = "TR330006100519786457841326"
    spaced = "TR33 0006 1005 1978 6457 8413 26"
    assert is_valid_turkish_iban(compact)
    entities = [entity for entity in RegexDetector().detect(f"{compact}; {spaced}") if entity.type == "IBAN"]
    assert len(entities) == 2
    assert all(entity.metadata["normalized"] == compact for entity in entities)


def test_invalid_iban_is_not_detected() -> None:
    assert not is_valid_turkish_iban("TR330006100519786457841327")
    assert "IBAN" not in detected_types("TR330006100519786457841327")


def test_luhn_card_detection_and_invalid_card_rejection() -> None:
    assert is_valid_luhn("4242 4242 4242 4242")
    assert not is_valid_luhn("4242 4242 4242 4241")
    assert not is_valid_luhn("0000 0000 0000 0000")
    assert "CREDIT_CARD" in detected_types("Card 4242-4242-4242-4242")
    assert "CREDIT_CARD" not in detected_types("Card 4242-4242-4242-4241")


def test_ipv4_accepts_valid_and_rejects_out_of_range() -> None:
    assert is_valid_ipv4("192.168.1.1")
    assert not is_valid_ipv4("999.999.999.999")
    assert "IP_ADDRESS" in detected_types("Server 192.168.1.1")
    assert "IP_ADDRESS" not in detected_types("Server 999.999.999.999")


def test_date_detector_validates_calendar_dates() -> None:
    assert is_valid_date("18.09.2026")
    assert is_valid_date("18/09/2026")
    assert is_valid_date("2026-09-18")
    assert not is_valid_date("31/02/2026")
    assert detected_types("Dates 18.09.2026 and 2026-09-18") == ["DATE", "DATE"]
    assert "DATE" not in detected_types("Impossible 31/02/2026")


def test_url_and_contextual_passport_detection() -> None:
    entities = RegexDetector().detect("Visit https://example.com/path. Pasaport no: U1234567")
    assert [(entity.type, entity.text) for entity in entities] == [
        ("URL", "https://example.com/path"),
        ("PASSPORT_ID", "U1234567"),
    ]
    assert "PASSPORT_ID" not in detected_types("U1234567 without a passport context")


def test_resolver_prefers_specific_entity_and_removes_duplicates() -> None:
    candidates = [
        DetectionCandidate("PERSON", "TR3300", 0, 6, 0.76, "ner"),
        DetectionCandidate("IBAN", "TR3300", 0, 6, 0.99, "regex"),
        DetectionCandidate("IBAN", "TR3300", 0, 6, 0.99, "regex"),
        DetectionCandidate("EMAIL", "a@b.co", 10, 16, 0.96, "regex"),
    ]
    resolved = EntityResolver().resolve(candidates)
    assert [entity.type for entity in resolved] == ["IBAN", "EMAIL"]


def test_detection_service_detects_semantic_and_multiple_entities_with_offsets() -> None:
    text = "Ahmet Yılmaz Ankara'da Acme Teknoloji A.Ş. için user@example.com ve 192.168.1.1 paylaştı."
    service = DetectionService()
    entities = service.detect(text)
    assert {entity.type for entity in entities} == {"PERSON", "LOCATION", "ORGANIZATION", "EMAIL", "IP_ADDRESS"}
    assert service.ner_available
    assert all(text[entity.start : entity.end] == entity.text for entity in entities)


def test_safe_mixed_language_and_unicode_prompt_has_no_false_positives() -> None:
    text = "Merhaba dünya, please summarize this public policy draft without identifiers."
    assert DetectionService().detect(text) == []


def test_ner_failure_keeps_deterministic_detection_available() -> None:
    class FailingNerDetector:
        available = True
        provider_name = "failing-test-provider"

        def detect(self, _: str) -> list[DetectionCandidate]:
            raise RuntimeError("simulated model load failure")

    service = DetectionService(ner_detector=FailingNerDetector())  # type: ignore[arg-type]
    entities = service.detect("Contact user@example.com")
    assert [entity.type for entity in entities] == ["EMAIL"]
    assert not service.ner_available


def test_masking_utilities_are_reusable_and_do_not_modify_input() -> None:
    assert mask_entity("PHONE", "+90 532 123 45 67") == "+90 *** *** ** **"
    assert mask_entity("EMAIL", "hassan@example.com") == "h*****@example.com"
    assert mask_entity("TC_ID", "12345678901") == "123*******01"
    assert mask_entity("IBAN", "TR330006100519786457841326") == "TR33********************26"
