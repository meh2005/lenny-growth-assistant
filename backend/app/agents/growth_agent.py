from claude_agent_sdk import ClaudeAgentOptions, query

from app.core.config import settings
from app.services.llm import llm_service


class GrowthAgent:
    """
    Agent orchestration layer for the Lenny Growth Assistant.

    Ollama is the default local/demo execution path.
    Claude Agent SDK is available when Anthropic is configured.
    """

    SYSTEM_PROMPT = """
You are the Lenny Growth Assistant.

You answer product and growth questions using evidence supplied
by the application from Lenny's Podcast transcripts.

GROUNDING RULES:

- The supplied transcript evidence is the only factual source.
- Do not use outside knowledge.
- Do not invent facts, definitions, examples, metrics,
  frameworks, results, or quotations.
- Do not treat the user's question as evidence.
- If the evidence does not support an important part of the
  question, explicitly say so.
- You may synthesize ideas from multiple transcript sources
  when the evidence supports that synthesis.
- Answer the user's actual question directly.
- Do not dump raw transcript excerpts unnecessarily.
"""

    async def generate_grounded_answer(
        self,
        question: str,
        evidence: str,
    ) -> str | None:
        """
        Generate a grounded answer through the configured agent/LLM.

        The application supplies retrieved evidence explicitly,
        preventing the model from treating outside knowledge as
        part of the knowledge base.
        """

        prompt = f"""
USER QUESTION:

{question}

RETRIEVED LENNY PODCAST TRANSCRIPT EVIDENCE:

{evidence}

TASK:

Answer the user's question using ONLY the transcript evidence above.

Every important factual claim based on transcript evidence must
include [Source N].

The source number must correspond to the numbered evidence.

If the evidence does not establish an important part of the answer,
say that the available Lenny Podcast evidence does not establish it.

Use concise Markdown.

Start with:

## Answer

Provide 3-6 useful points when supported by the evidence.

Do not create quotations.

Return ONLY the answer.
"""

        try:
            if (
                settings.MODEL_PROVIDER.lower() == "anthropic"
                and settings.ANTHROPIC_API_KEY
            ):
                return await self._claude_agent(prompt)

            # Default local execution path.
            return await llm_service.generate(
                [
                    {
                        "role": "system",
                        "content": self.SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ]
            )

        except Exception as error:
            print(f"[GrowthAgent] Generation failed: {error}")
            return None

    async def _claude_agent(self, prompt: str) -> str | None:
        """
        Execute the same grounded task through Claude Agent SDK.

        Claude is optional. Local Ollama remains the default so the
        application can run without cloud credentials.
        """

        options = ClaudeAgentOptions(
            system_prompt=self.SYSTEM_PROMPT,
            model=settings.ANTHROPIC_MODEL,
            max_turns=3,
            permission_mode="dontAsk",
        )

        output = []

        async for message in query(
            prompt=prompt,
            options=options,
        ):
            if hasattr(message, "content"):
                for block in message.content:
                    if hasattr(block, "text"):
                        output.append(block.text)

        result = "\n".join(output).strip()

        return result or None


growth_agent = GrowthAgent()