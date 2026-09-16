import json
import re
from uuid import UUID
from app.agents.growth_agent import growth_agent
from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from app.db.database import get_db
from app.db.models import ChatSession, ChatMessage
from app.rag.retriever import retrieve_chunks
from app.agents.artifact_agent import build_artifact_html
from app.agents.ship30_skill import (
    build_ship30_article,
    _extract_topic,
)
from app.services.llm import llm_service
from app.core.errors import api_error

router = APIRouter(prefix="/api/chat", tags=["Chat"])


FALLBACK = (
    "The available Lenny Podcast transcripts don't provide "
    "enough information to answer this confidently."
)


class ChatRequest(BaseModel):
    session_id: UUID
    message: str  = Field(
        min_length=1,
        max_length=5000,
    )


class SourceResponse(BaseModel):
    episode_title: str
    source_id: str
    chunk_index: int
    content: str


class ArtifactResponse(BaseModel):
    title: str
    type: str
    html: str


class ChatResponse(BaseModel):
    session_id: UUID
    response: str
    sources: list[SourceResponse]
    artifact: ArtifactResponse | None = None


def _get_conversation_history(
    db: Session,
    session_id: UUID,
    limit: int = 8,
) -> list[ChatMessage]:
    """
    Get recent conversation messages so follow-up questions
    can be interpreted using the existing session context.
    """

    messages = (
        db.query(ChatMessage)
        .filter(
            ChatMessage.session_id == session_id
        )
        .order_by(
            ChatMessage.created_at.desc()
        )
        .limit(limit)
        .all()
    )

    return list(reversed(messages))


def _build_context_text(
    messages: list[ChatMessage],
) -> str:
    """
    Build a compact conversation history for query rewriting.
    """

    if not messages:
        return ""

    lines = []

    for message in messages:

        role = message.role.upper()

        content = message.content.strip()

        if len(content) > 1200:
            content = (
                content[:1200]
                .rsplit(" ", 1)[0]
                + "..."
            )

        lines.append(
            f"{role}: {content}"
        )

    return "\n".join(lines)


async def _rewrite_query(
    current_message: str,
    history: list[ChatMessage],
) -> str:
    """
    Rewrite the user's latest message into a standalone
    retrieval query using recent conversation context.

    This model call is only used for query rewriting.
    It does not answer the user's question.
    """

    if not history:
        return current_message

    conversation = _build_context_text(history)

    prompt = f"""
Rewrite the user's latest message into a concise standalone
search query for a knowledge base containing Lenny Podcast
transcripts.

CONVERSATION:

{conversation}

LATEST USER MESSAGE:

{current_message}

RULES:

- Resolve references such as "that", "this", "it", "they",
  "those", and "the previous answer".
- Preserve the user's actual intent.
- Include important context from previous turns when necessary.
- Do not answer the question.
- Do not add facts.
- Do not invent terminology.
- Return ONLY the rewritten search query.
"""

    try:

        result = await llm_service.generate(
            [
                {
                    "role": "system",
                    "content": (
                        "You rewrite follow-up questions into "
                        "standalone search queries. "
                        "Return only the query."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ]
        )

        result = result.strip()

        if result:
            return result

    except Exception as error:

        print(
            f"[Chat] Query rewrite failed: {error}"
        )

    return current_message


def _build_evidence(
    chunks: list,
) -> str:
    """
    Convert retrieved transcript chunks into clearly numbered
    evidence for the answering model.
    """

    evidence = []

    for index, chunk in enumerate(
        chunks[:5],
        start=1,
    ):

        content = re.sub(
            r"\s+",
            " ",
            chunk.content,
        ).strip()

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

Episode:
{chunk.episode_title}

Source ID:
{chunk.source_id}

Chunk:
{chunk.chunk_index}

TRANSCRIPT EVIDENCE:

{content}
"""
        )

    return "\n".join(evidence)


async def _generate_grounded_answer(
    question: str,
    chunks: list,
) -> str | None:
    """
    Generate a grounded conversational answer through the
    Growth Agent orchestration layer.
    """

    evidence = _build_evidence(chunks)

    answer = await growth_agent.generate_grounded_answer(
        question=question,
        evidence=evidence,
    )

    if not answer:
        return None

    # Remove accidental Markdown code fences.
    answer = re.sub(
        r"^```(?:markdown)?\s*",
        "",
        answer,
        flags=re.IGNORECASE,
    )

    answer = re.sub(
        r"\s*```$",
        "",
        answer,
    )

    return answer.strip()


def _build_extract_fallback(
    chunks: list,
) -> str:
    """
    Safe fallback if the local model cannot generate an answer.
    """

    answer_parts = [
        "## Answer",
        "",
        "The local model could not synthesize the answer, "
        "so here are the most relevant transcript findings:",
        "",
    ]

    for i, chunk in enumerate(
        chunks[:3],
        start=1,
    ):

        text = chunk.content.strip()

        if len(text) > 900:
            text = (
                text[:900]
                .rsplit(" ", 1)[0]
                + "..."
            )

        answer_parts.append(
            f"- {text} [Source {i}]"
        )

    return "\n".join(answer_parts)


def _append_authoritative_sources(
    answer: str,
    chunks: list,
) -> str:
    """
    Replace any model-generated Sources section with an
    authoritative source list generated directly from the DB.
    """

    answer = re.sub(
        r"\n#+\s*Sources\s*\n.*$",
        "",
        answer,
        flags=re.IGNORECASE | re.DOTALL,
    )

    source_lines = [
        f"- [Source {i}] {chunk.episode_title} — "
        f"`{chunk.source_id}`, chunk {chunk.chunk_index}"
        for i, chunk in enumerate(
            chunks[:5],
            start=1,
        )
    ]

    return (
        answer.rstrip()
        + "\n\n## Sources\n\n"
        + "\n".join(source_lines)
    )


def _markdown_to_basic_html(
    markdown: str,
) -> str:
    """
    Convert generated Markdown into basic HTML for the
    Artifact Viewer.
    """

    lines = markdown.splitlines()

    html = []

    in_unordered_list = False
    in_ordered_list = False

    def close_lists():

        nonlocal in_unordered_list
        nonlocal in_ordered_list

        if in_unordered_list:
            html.append("</ul>")
            in_unordered_list = False

        if in_ordered_list:
            html.append("</ol>")
            in_ordered_list = False

    for line in lines:

        stripped = line.strip()

        if not stripped:
            continue

        if stripped.startswith("# "):

            close_lists()

            html.append(
                f"<h1>{_escape_html(stripped[2:])}</h1>"
            )

        elif stripped.startswith("## "):

            close_lists()

            html.append(
                f"<h2>{_escape_html(stripped[3:])}</h2>"
            )

        elif stripped.startswith("### "):

            close_lists()

            html.append(
                f"<h3>{_escape_html(stripped[4:])}</h3>"
            )

        elif stripped.startswith("- "):

            if in_ordered_list:
                html.append("</ol>")
                in_ordered_list = False

            if not in_unordered_list:
                html.append("<ul>")
                in_unordered_list = True

            html.append(
                f"<li>{_escape_html(stripped[2:])}</li>"
            )

        elif re.match(
            r"^\d+\.\s+",
            stripped,
        ):

            if in_unordered_list:
                html.append("</ul>")
                in_unordered_list = False

            if not in_ordered_list:
                html.append("<ol>")
                in_ordered_list = True

            content = re.sub(
                r"^\d+\.\s+",
                "",
                stripped,
            )

            html.append(
                f"<li>{_escape_html(content)}</li>"
            )

        elif stripped.startswith("> "):

            close_lists()

            html.append(
                f"<blockquote>"
                f"{_escape_html(stripped[2:])}"
                f"</blockquote>"
            )

        else:

            close_lists()

            html.append(
                f"<p>{_escape_html(stripped)}</p>"
            )

    close_lists()

    return "\n".join(html)


def _escape_html(
    text: str,
) -> str:
    """Escape HTML-sensitive characters."""

    return (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


@router.post(
    "",
    response_model=ChatResponse,
)
async def chat(
    data: ChatRequest,
    db: Session = Depends(get_db),
):

    # =========================================================
    # Find session
    # =========================================================

    session = (
        db.query(ChatSession)
        .filter(
            ChatSession.id == data.session_id
        )
        .first()
    )

    if not session:

        raise api_error(    404,    "SESSION_NOT_FOUND",    "The requested chat session does not exist.",)

    # =========================================================
    # Get previous conversation BEFORE saving current message
    # =========================================================

    history = _get_conversation_history(
        db,
        session.id,
        limit=8,
    )

    # =========================================================
    # Save user message
    # =========================================================

    user_message = ChatMessage(
        session_id=session.id,
        role="user",
        content=data.message,
    )

    db.add(user_message)
    db.commit()

    # =========================================================
    # Detect request type
    # =========================================================

    question = data.message.lower()

    artifact_terms = [
        "create an artifact",
        "create a landing page",
        "build a landing page",
        "generate a landing page",
        "create html",
        "create an html",
        "generate html",
        "generate an html",
        "build html",
        "build an html",
        "create a webpage",
        "generate a webpage",
        "create a web page",
        "generate a web page",
        "make a landing page",
        "make an html",
    ]

    ship30_terms = [
        "30 for 30",
        "30-for-30",
        "ship 30",
        "ship30",
        "write an article",
        "write a 30",
        "create an article",
        "generate an article",
        "write a post",
        "create a post",
    ]

    is_artifact_request = any(
        term in question
        for term in artifact_terms
    )

    is_ship30_request = any(
        term in question
        for term in ship30_terms
    )

    # =========================================================
    # Build retrieval query
    # =========================================================

    if is_ship30_request:

        retrieval_query = _extract_topic(
            data.message
        )

    elif history:

        retrieval_query = await _rewrite_query(
            current_message=data.message,
            history=history,
        )

    else:

        retrieval_query = data.message

    print(
        f"[Chat] Retrieval query: {retrieval_query}"
    )

    # =========================================================
    # Retrieve transcript evidence
    # =========================================================

    try:

        chunks = retrieve_chunks(
            db,
            retrieval_query,
            top_k=5,
        )

    except Exception as error:

        print(
            f"[Chat] Retrieval failed: {error}"
        )

        raise api_error(503,"RETRIEVAL_UNAVAILABLE","The transcript knowledge base is temporarily unavailable.",)

    # =========================================================
    # No evidence
    # =========================================================

    if not chunks:

        answer = FALLBACK

        db.add(
            ChatMessage(
                session_id=session.id,
                role="assistant",
                content=answer,
                sources=json.dumps([]),
            )
        )

        db.commit()

        return ChatResponse(
            session_id=session.id,
            response=answer,
            sources=[],
            artifact=None,
        )

    artifact = None

    # =========================================================
    # SHIP 30 FOR 30
    # =========================================================

    if is_ship30_request:

        actual_topic = _extract_topic(
            data.message
        )

        article = await build_ship30_article(
            topic=actual_topic,
            chunks=chunks,
        )

        answer = _append_authoritative_sources(
            article,
            chunks,
        )

        artifact_html = build_artifact_html(
            title=(
                f"{actual_topic.title()} "
                f"— Ship 30 for 30"
            ),
            content=_markdown_to_basic_html(
                article
            ),
        )

        artifact = ArtifactResponse(
            title=(
                f"{actual_topic.title()} "
                f"— Ship 30 for 30"
            ),
            type="HTML Preview",
            html=artifact_html,
        )

    # =========================================================
    # NORMAL GROUNDED Q&A
    # =========================================================

    else:

        answer = await _generate_grounded_answer(
            question=retrieval_query,
            chunks=chunks,
        )

        if not answer:

            answer = _build_extract_fallback(
                chunks
            )

        answer = _append_authoritative_sources(
            answer,
            chunks,
        )

    # =========================================================
    # GENERIC HTML ARTIFACT
    # =========================================================

    if (
        is_artifact_request
        and not is_ship30_request
    ):

        artifact_content = """
<h2>Growth Experiment</h2>

<p>
Use this experiment to reduce the time between signup
and the user's first meaningful product value.
</p>

<h2>Experiment</h2>

<ul>
  <li>Ask the user a small number of targeted questions.</li>
  <li>Identify their primary use case.</li>
  <li>Immediately provide a relevant starting template.</li>
  <li>Measure the time from signup to meaningful product usage.</li>
</ul>

<div class="takeaway">
  <strong>Key takeaway</strong>
  Reduce the distance between signup and the moment
  when the user experiences meaningful value.
</div>
"""

        artifact_html = build_artifact_html(
            title="Activation Growth Experiment",
            content=artifact_content,
        )

        artifact = ArtifactResponse(
            title="Activation Growth Experiment",
            type="HTML Preview",
            html=artifact_html,
        )

        answer += """

## Artifact

I've created an HTML artifact based on the activation principles
found in the retrieved transcript evidence. Open the Artifact Viewer
to preview it.
"""

    # =========================================================
    # Save assistant message + source trace
    # =========================================================

    source_data = [
        {
            "episode_title": chunk.episode_title,
            "source_id": chunk.source_id,
            "chunk_index": chunk.chunk_index,
            "content": chunk.content,
        }
        for chunk in chunks
    ]

    db.add(
        ChatMessage(
            session_id=session.id,
            role="assistant",
            content=answer,
            sources=json.dumps(source_data),
        )
    )

    db.commit()

    # =========================================================
    # Response
    # =========================================================

    return ChatResponse(
        session_id=session.id,
        response=answer,
        sources=[
            SourceResponse(
                episode_title=chunk.episode_title,
                source_id=chunk.source_id,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
            )
            for chunk in chunks
        ],
        artifact=artifact,
    )