from __future__ import annotations

import pytest

from pipeline.document_reader import read_document
from pipeline.extractor import ConfigurableLLMExtractor, parse_llm_payload


VALID_RESPONSE = """
{
  "nodes": [
    {
      "type": "Product",
      "data": {
        "slug": "product:test",
        "name": "Test",
        "status": "active",
        "visibility": "internal",
        "source_document_id": "doc:test",
        "source_file": "test.md",
        "source_excerpt": "Test product",
        "confidence": "0.90"
      }
    },
    {
      "type": "Feature",
      "data": {
        "slug": "feature:test:one",
        "name": "One",
        "product_area": "Test",
        "description": "Feature one",
        "feature_type": "capability",
        "status": "active",
        "visibility": "internal",
        "source_document_id": "doc:test",
        "source_file": "test.md",
        "source_excerpt": "Feature one",
        "confidence": "0.90"
      }
    }
  ],
  "edges": [
    {
      "edge": "HasFeature",
      "from": "product:test",
      "to": "feature:test:one",
      "source_document_id": "doc:test",
      "source_file": "test.md",
      "source_excerpt": "Feature one",
      "confidence": "0.90"
    }
  ]
}
"""


def test_parse_llm_payload_validates_structured_output():
    payload = parse_llm_payload(VALID_RESPONSE)
    assert payload.nodes[0].slug == "product:test"
    assert payload.edges[0].edge == "HasFeature"


def test_parse_llm_payload_rejects_invalid_entity_type():
    with pytest.raises(ValueError, match="Unsupported node type"):
        parse_llm_payload('{"nodes":[{"type":"Secret","data":{"slug":"secret:x"}}],"edges":[]}')


def test_missing_api_key_has_clear_error():
    extractor = ConfigurableLLMExtractor("gemini", "gemini-1.5-flash", "")
    with pytest.raises(RuntimeError, match="LLM_API_KEY"):
        extractor.extract(read_document("seed-data/stockly-product-overview.md"))


def test_malformed_response_retries_then_succeeds(monkeypatch):
    calls = []
    extractor = ConfigurableLLMExtractor("gemini", "gemini-1.5-flash", "test-key", max_attempts=2)

    def fake_generate(document, attempt, previous_error):
        calls.append((attempt, previous_error))
        return "{not-json" if attempt == 1 else VALID_RESPONSE

    monkeypatch.setattr(extractor, "_generate", fake_generate)
    payload = extractor.extract(read_document("seed-data/stockly-product-overview.md"))
    assert len(calls) == 2
    assert payload.nodes[0].slug == "product:test"


def test_no_silent_fallback_when_llm_output_stays_invalid(monkeypatch):
    extractor = ConfigurableLLMExtractor("gemini", "gemini-1.5-flash", "test-key", max_attempts=2)
    monkeypatch.setattr(extractor, "_generate", lambda document, attempt, previous_error: "{not-json")
    with pytest.raises(RuntimeError, match="malformed structured output"):
        extractor.extract(read_document("seed-data/stockly-product-overview.md"))
