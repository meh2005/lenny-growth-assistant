import pytest
from app.agents.growth_agent import GrowthAgent


@pytest.mark.anyio
async def test_growth_agent_includes_grounding_evidence(monkeypatch):
    captured = {}

    async def fake_generate(messages):
        captured["messages"] = messages
        return "## Answer\n\nUse the evidence provided. [Source 1]"

    from app.agents import growth_agent as module
    monkeypatch.setattr(module.llm_service, "generate", fake_generate)

    agent = GrowthAgent()

    result = await agent.generate_grounded_answer(
        question="How can I improve activation?",
        evidence="[Source 1] Activation improves when users reach core value quickly."
    )

    assert result is not None
    assert "[Source 1]" in result
    assert "Activation improves" in captured["messages"][1]["content"]
