import re

from app.services.llm import llm_service


SHIP_30_FOR_30_SKILL = """
You are writing a Ship 30 for 30 style product/growth article.

Your job is to transform the supplied transcript evidence into a
clear, useful article.

STRICT GROUNDING RULES:

- The transcript evidence supplied by the application is your ONLY
  factual source.
- Do NOT use outside knowledge.
- Do NOT invent definitions.
- Do NOT invent companies, products, metrics, examples, frameworks,
  results, or recommendations.
- Do NOT assume that the topic is defined by its name.
- If the transcript evidence does not explain something, say that the
  available evidence does not establish it.
- You may synthesize ideas from multiple transcript excerpts when the
  excerpts genuinely support the synthesis.
- Never create a quotation unless the exact wording appears in the
  supplied transcript.
- Do not create a Sources section. The application adds that section
  from the database.

WRITING STYLE:

- Approximately 1,000–1,250 words when enough evidence exists.
- Strong opening hook.
- Clear narrative.
- Short paragraphs.
- Descriptive headings.
- Skimmable formatting.
- Practical takeaways.
- Specific examples only when supported by evidence.

REQUIRED STRUCTURE:

# Headline

Opening hook.

## Why this matters

Explain what the retrieved evidence says about the topic.

## The key insight

Synthesize the strongest supported ideas.

## How to apply it

Turn supported ideas into practical actions. Clearly distinguish
source-supported recommendations from your own synthesis.

## What to watch for

Discuss limitations that are actually supported by the evidence.
Do not invent limitations.

## Practical takeaway

End with concise, useful takeaways.

CITATIONS:

Every important factual claim derived from transcript evidence must
include [Source N].

The source numbers must correspond to the numbered evidence supplied
by the application.

Do not invent source names or source titles.
"""


def _extract_topic(topic: str) -> str:
    """Extract the actual article topic from the user's request."""

    patterns = [
        r"write\s+(?:a\s+)?30\s*(?:for|-)?\s*30\s+article\s+about\s+(.+)",
        r"write\s+(?:a\s+)?30\s*(?:for|-)?\s*30\s+about\s+(.+)",
        r"create\s+(?:a\s+)?30\s*(?:for|-)?\s*30\s+article\s+about\s+(.+)",
        r"generate\s+(?:a\s+)?30\s*(?:for|-)?\s*30\s+article\s+about\s+(.+)",
        r"write\s+an?\s+article\s+about\s+(.+)",
        r"create\s+an?\s+article\s+about\s+(.+)",
        r"generate\s+an?\s+article\s+about\s+(.+)",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            topic.strip(),
            flags=re.IGNORECASE,
        )

        if match:

            extracted = match.group(1).strip()

            extracted = re.sub(
                r"[.!?]+$",
                "",
                extracted,
            )

            return extracted

    return topic.strip().rstrip(".!? ")


def _build_evidence(chunks: list) -> str:
    """
    Build a compact, explicitly numbered evidence block.

    Source metadata comes directly from the database.
    """

    evidence = []

    for index, chunk in enumerate(chunks[:5], start=1):

        content = re.sub(
            r"\s+",
            " ",
            chunk.content,
        ).strip()

        # Keep the prompt manageable for the local model.
        if len(content) > 1800:
            content = (
                content[:1800]
                .rsplit(" ", 1)[0]
                + "..."
            )

        evidence.append(
            f"""
========================
SOURCE {index}
========================
Episode: {chunk.episode_title}
Source ID: {chunk.source_id}
Chunk: {chunk.chunk_index}

TRANSCRIPT EVIDENCE:
{content}
"""
        )

    return "\n".join(evidence)


def _remove_model_sources(article: str) -> str:
    """
    Remove any Sources section hallucinated by the LLM.

    The backend will add the authoritative database sources itself.
    """

    article = re.sub(
        r"\n#+\s*Sources\s*\n.*$",
        "",
        article,
        flags=re.IGNORECASE | re.DOTALL,
    )

    article = re.sub(
        r"\n#+\s*References\s*\n.*$",
        "",
        article,
        flags=re.IGNORECASE | re.DOTALL,
    )

    return article.strip()


def _clean_article(article: str) -> str:
    """Clean common formatting problems."""

    article = article.strip()

    article = re.sub(
        r"^```(?:markdown)?\s*",
        "",
        article,
        flags=re.IGNORECASE,
    )

    article = re.sub(
        r"\s*```$",
        "",
        article,
    )

    article = _remove_model_sources(article)

    return article.strip()


async def build_ship30_article(
    topic: str,
    chunks: list,
) -> str:
    """
    Generate a grounded Ship 30 for 30 article.

    Ollama performs synthesis, but factual evidence and source
    metadata come from the retrieved transcript chunks.
    """

    actual_topic = _extract_topic(topic)

    if not chunks:

        return (
            f"# {actual_topic.title()}\n\n"
            "The available Lenny Podcast transcripts do not contain "
            "enough relevant evidence to write a grounded article "
            "about this topic."
        )

    evidence = _build_evidence(chunks)

    prompt = f"""
ARTICLE TOPIC:

{actual_topic}


TRANSCRIPT EVIDENCE:

{evidence}


TASK:

Write a Ship 30 for 30 style article specifically about:

{actual_topic}

Use ONLY the transcript evidence above.

Before writing, reason internally about which pieces of evidence
actually relate to the topic.

IMPORTANT:

The topic is NOT evidence.

For example, if the topic is "product activation", do not define
product activation from general product-management knowledge.

Only describe activation using information that actually appears
in the supplied transcripts.

If the evidence only partially covers the topic, write a narrower
article around what the evidence supports and explicitly acknowledge
the limitation.

Do NOT:

- invent a definition
- invent benefits
- invent companies
- invent metrics
- invent examples
- invent frameworks
- invent results
- invent quotes
- invent source titles
- add a Sources section

CITATION FORMAT:

Use [Source 1], [Source 2], etc. immediately after supported claims.

Example:

The transcript describes activation as one of several areas a
product team may focus on. [Source 1]

Do NOT cite a source merely because it was retrieved. The source
must actually support the statement.

Write approximately 1,000–1,250 words if the evidence supports that
much content. Do not add unsupported material merely to reach the
word count.

Return ONLY the Markdown article.
"""

    try:

        article = await llm_service.generate(
            [
                {
                    "role": "system",
                    "content": SHIP_30_FOR_30_SKILL,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ]
        )

    except Exception as error:

        print(
            f"[Ship30] LLM generation failed: {error}"
        )

        return (
            f"# {actual_topic.title()}\n\n"
            "The local language model could not generate the article "
            "at this time. The retrieved transcript evidence is "
            "available through the Sources panel."
        )

    article = _clean_article(article)

    if not article:

        return (
            f"# {actual_topic.title()}\n\n"
            "The available transcript evidence was not sufficient "
            "to generate an article."
        )

    return article