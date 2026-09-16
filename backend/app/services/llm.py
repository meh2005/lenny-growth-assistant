import logging

import httpx
from anthropic import AsyncAnthropic

from app.core.config import settings


logger = logging.getLogger(__name__)


class LLMService:
    async def generate(
        self,
        messages: list[dict[str, str]],
    ) -> str:
        provider = settings.MODEL_PROVIDER.lower()

        if provider == "ollama":
            return await self._ollama(messages)

        if provider == "anthropic":
            return await self._anthropic(messages)

        raise RuntimeError(
            f"Unsupported model provider: {settings.MODEL_PROVIDER}"
        )

    async def _ollama(
        self,
        messages: list[dict[str, str]],
    ) -> str:
        payload = {
            "model": settings.OLLAMA_MODEL,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "top_p": 0.8,
                "num_predict": 1400,
            },
        }

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(
                    connect=10.0,
                    read=300.0,
                    write=30.0,
                    pool=10.0,
                )
            ) as client:
                response = await client.post(
                    f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/chat",
                    json=payload,
                )

            response.raise_for_status()

            data = response.json()
            content = data.get("message", {}).get("content")

            if not content:
                raise RuntimeError(
                    "Ollama returned an empty response."
                )

            return content

        except httpx.ConnectError as error:
            logger.error("Ollama connection failed: %s", error)
            raise RuntimeError(
                "Ollama is unavailable. Make sure Ollama is running."
            ) from error

        except httpx.TimeoutException as error:
            logger.error("Ollama request timed out: %s", error)
            raise RuntimeError(
                "The Ollama model timed out while generating a response."
            ) from error

        except httpx.HTTPStatusError as error:
            logger.error(
                "Ollama returned HTTP %s",
                error.response.status_code,
            )
            raise RuntimeError(
                "Ollama returned an error while generating the response."
            ) from error

        except (KeyError, TypeError, ValueError) as error:
            logger.error("Invalid Ollama response: %s", error)
            raise RuntimeError(
                "Ollama returned an invalid response."
            ) from error

    async def _anthropic(
        self,
        messages: list[dict[str, str]],
    ) -> str:
        if not settings.ANTHROPIC_API_KEY:
            raise RuntimeError(
                "Anthropic provider selected but "
                "ANTHROPIC_API_KEY is not configured."
            )

        system_messages = [
            message["content"]
            for message in messages
            if message["role"] == "system"
        ]

        conversation_messages = [
            {
                "role": message["role"],
                "content": message["content"],
            }
            for message in messages
            if message["role"] != "system"
        ]

        client = AsyncAnthropic(
            api_key=settings.ANTHROPIC_API_KEY
        )

        try:
            response = await client.messages.create(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=1400,
                temperature=0.2,
                system="\n\n".join(system_messages),
                messages=conversation_messages,
            )

            content = "".join(
                block.text
                for block in response.content
                if hasattr(block, "text")
            )

            if not content:
                raise RuntimeError(
                    "Anthropic returned an empty response."
                )

            return content

        except Exception as error:
            logger.error(
                "Anthropic generation failed: %s",
                error,
            )
            raise RuntimeError(
                "The Anthropic model is currently unavailable."
            ) from error


llm_service = LLMService()