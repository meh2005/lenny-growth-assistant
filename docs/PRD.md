# Product Requirements Document
# The Lenny Growth Assistant

## 1. Product Overview

The Lenny Growth Assistant is a full-stack AI conversational assistant that helps
product and growth practitioners learn from Lenny's Podcast transcripts.

Users can ask product and growth questions, continue conversations across a
session, and generate written content or visual artifacts grounded in the
transcript knowledge base.

The system is designed to prioritize grounded answers rather than general
model knowledge.

---

## 2. User and Problem

### Target Users

- Product managers
- Growth practitioners
- Founders
- Product and engineering students
- Anyone learning product and growth concepts from Lenny's Podcast

### Problem

Product and growth knowledge is distributed across many long-form podcast
transcripts. Finding the relevant discussion and applying it to a specific
problem requires significant manual searching.

The assistant should reduce this effort by allowing users to ask questions
using natural language and receive answers connected to relevant transcript
sources.

---

## 3. Product Goals

The product should:

1. Answer product and growth questions using Lenny's Podcast transcripts.
2. Maintain conversation context within independent sessions.
3. Show the sources used to produce an answer.
4. Clearly acknowledge when the transcript material does not support an answer.
5. Generate useful written content using the Ship 30 for 30 writing principles.
6. Generate HTML artifacts that can be previewed safely inside the application.
7. Support local Ollama inference for the demo.
8. Provide an optional cloud-model configuration.
9. Persist sessions, messages, and transcript chunks in PostgreSQL.

---

## 4. Success Metrics

The following metrics will be used to evaluate the system:

### Grounding Success Rate

At least 90% of answers in a manually curated evaluation set of 20 product and
growth questions should:

- use relevant transcript evidence,
- provide source references,
- avoid unsupported factual claims.

### Unsupported Question Handling

For questions that cannot be answered from the transcript knowledge base,
the assistant should explicitly state that the available material does not
provide sufficient evidence.

### Artifact Success Rate

At least 95% of generated artifact requests in the evaluation set should
produce a renderable artifact without breaking the application UI.

### Reliability

The API should return structured errors for:

- invalid requests,
- unavailable Ollama,
- unavailable retrieval,
- missing cloud credentials,
- model timeouts,
- unexpected application errors.

---

## 5. Assumptions

- Lenny's Podcast transcripts are the primary knowledge source.
- Users value source traceability over answers based on unrestricted model
  knowledge.
- Ollama is available locally during the required demo.
- PostgreSQL with pgvector is available for persistence and retrieval.
- Generated HTML is untrusted content and must be isolated before rendering.

---

## 6. Scope

### In Scope

- Conversational chat
- Session creation and persistence
- PostgreSQL persistence
- Transcript ingestion
- Embedding-based retrieval
- Grounded answer generation
- Source trace display
- Ollama model support
- Anthropic model configuration
- Ship 30 for 30 writing skill
- Markdown/HTML artifact generation
- Sandboxed artifact preview
- API health endpoint
- Structured API errors
- Automated tests
- Docker Compose configuration
- Documentation

### Out of Scope

- User accounts and production authentication
- Multi-tenant permissions
- Mobile applications
- Fine-tuning a language model
- Training custom embedding models
- Editing the original podcast transcripts
- General-purpose web search

---

## 7. User Experience

### Chat

The user starts a session and asks a product or growth question.

The system:

1. Receives the question.
2. Retrieves relevant transcript chunks.
3. Passes the retrieved evidence to the growth agent.
4. Generates a grounded response.
5. Displays the answer and source references.
6. Persists the conversation.

### Follow-up Questions

Follow-up messages use the same session so the assistant can retain
conversation context.

### Artifact Generation

When the user requests a visual or written artifact, the system generates
the artifact and displays it in the Artifact Viewer beside the conversation.

The user can switch between the rendered preview and the generated source.

---

## 8. Knowledge Base

The knowledge base contains Lenny's Podcast transcripts.

The ingestion pipeline:

1. Reads transcript files.
2. Splits transcripts into overlapping chunks.
3. Generates embeddings using `BAAI/bge-small-en-v1.5`.
4. Stores chunks and embeddings in PostgreSQL with pgvector.
5. Uses vector similarity to retrieve relevant evidence for each question.

The current dataset contains approximately 303 episodes and 4,733 indexed
transcript chunks.

Each retrieved chunk retains its episode/source information so the assistant
can provide source traceability.

---

## 9. Agent Architecture

The application uses a dedicated growth agent.

The agent is instructed to:

- use transcript evidence,
- avoid unsupported outside knowledge,
- cite retrieved evidence,
- preserve conversational context,
- acknowledge insufficient evidence.

Ollama is the default local provider.

Anthropic is supported as an alternative provider when configured.

---

## 10. Ship 30 for 30 Skill

A dedicated writing skill is provided for the Ship 30 for 30 workflow.

The skill uses transcript evidence and writing principles including:

- strong opening hook,
- clear narrative,
- short paragraphs,
- skimmable structure,
- practical takeaways,
- grounded claims.

The generated content is intended to be useful as a standalone written piece
while remaining grounded in the available transcript evidence.

---

## 11. Artifact Security

Generated HTML is treated as untrusted content.

Artifacts are rendered inside a sandboxed iframe rather than directly inside
the application's DOM.

The backend also removes potentially executable elements and event-handler
attributes before sending generated HTML to the frontend.

This reduces the risk of generated content executing arbitrary browser code.

---

## 12. Risks and Tradeoffs

### Hallucination

Even with retrieval, a language model can produce unsupported claims.

Mitigation:

- transcript-only system instructions,
- retrieved evidence,
- source trace,
- explicit unsupported-answer behavior.

### Latency

Local LLM inference can be slower than cloud inference, especially on
machines without a dedicated GPU.

Tradeoff:

The demo prioritizes local reproducibility and privacy over minimum latency.

### Cost

Cloud model usage can introduce API costs.

Tradeoff:

Ollama provides a local zero-API-cost path for the demo.

### Local Model Quality

Smaller local models may produce less detailed answers than larger cloud
models.

Tradeoff:

The system supports a configurable provider so the same application can use
a cloud model when higher generation quality is required.

### Data Leakage

Retrieved transcript content is passed to the configured model provider.

Mitigation:

- local Ollama support,
- controlled provider configuration,
- no secrets committed to the repository.

### Unsafe Rendering

Generated HTML can contain unsafe content.

Mitigation:

- HTML sanitization,
- sandboxed iframe rendering,
- no direct execution in the main application DOM.

---

## 13. Acceptance Criteria

The product is considered functional when:

- A user can create a session.
- A user can send a question.
- Relevant transcript evidence is retrieved.
- The response is grounded in that evidence.
- Sources are visible to the user.
- Follow-up questions remain within the same session.
- Unsupported questions are acknowledged appropriately.
- Ollama can be used locally.
- The Ship 30 skill generates grounded written content.
- Artifacts render inside the application.
- Generated HTML is isolated.
- PostgreSQL stores sessions and messages.
- Health and error endpoints behave correctly.
- Automated tests pass.