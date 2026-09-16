from app.api.chat import _build_evidence


def test_build_evidence_numbers_sources():
    chunks = [
        type("Chunk", (), {
            "episode_title": "Test Episode",
            "guest_name": "Test Guest",
            "source_id": "test-1",
            "source_url": "https://example.com",
            "content": "Activation improves when users reach the core value quickly.",
            "chunk_index": 3,
        })(),
        type("Chunk", (), {
            "episode_title": "Second Episode",
            "guest_name": "Another Guest",
            "source_id": "test-2",
            "source_url": "https://example.com/2",
            "content": "Teams should measure meaningful user behavior.",
            "chunk_index": 5,
        })(),
    ]

    evidence = _build_evidence(chunks)

    assert "SOURCE 1" in evidence
    assert "SOURCE 2" in evidence
    assert "Test Episode" in evidence
    assert "Second Episode" in evidence
    assert "Activation improves" in evidence
