# Design Document
# The Lenny Growth Assistant

## 1. Design Goals

The application is designed around four principles:

1. Ground answers in Lenny's Podcast transcripts.
2. Keep the conversational experience simple.
3. Make sources visible and traceable.
4. Keep generated artifacts isolated from the main application.

---

## 2. User Flow

```text
User
  |
  v
Chat UI
  |
  v
FastAPI Backend
  |
  +----> Session / Message Persistence
  |
  v
Growth Agent
  |
  v
Transcript Retriever
  |
  v
PostgreSQL + pgvector
  |
  v
Relevant Transcript Chunks
  |
  v
LLM Provider
  |
  v
Grounded Response
  |
  +----> Source Panel
  |
  +----> Artifact Viewer

  ## 3. Frontend Design

The frontend is implemented using React.

### Main Components

App
- Sidebar
- Chat
- SourcePanel
- ArtifactViewer

### Sidebar

The sidebar provides:

- New conversation
- Existing sessions
- Session deletion

### Chat

The chat area displays:

- User messages
- Assistant messages
- Markdown responses
- Suggested questions

### Source Panel

The Source Panel displays transcript sources associated with an assistant
response.

### Artifact Viewer

The Artifact Viewer displays generated artifacts beside the conversation.

Users can switch between Preview and Code views.


## 4. Backend Design

The backend uses FastAPI.

The main API areas are:

- /api/health
- /api/sessions
- /api/chat

The backend handles:

- Request validation
- Session management
- Message persistence
- Transcript retrieval
- Agent execution
- Source tracking
- LLM provider selection
- Structured errors


## 5. Session Design

Every conversation has a unique session ID.

A session can contain multiple chat messages.

The database stores:

- Chat sessions
- User messages
- Assistant messages
- Source traces

This keeps conversations independent.

Follow-up questions use the same session so previous conversation context can
be retained.


## 6. RAG Design

The knowledge base consists of Lenny's Podcast transcripts.

### Ingestion Pipeline

Transcript Files
    |
    v
Text Extraction
    |
    v
Chunking
    |
    v
Embedding Generation
    |
    v
PostgreSQL + pgvector

The current knowledge base contains approximately:

- 303 podcast episodes
- 4,733 transcript chunks

### Chunking

Current configuration:

- Chunk size: 1200 characters
- Overlap: 200 characters

The overlap helps preserve context between neighboring chunks.

### Embeddings

The embedding model is:

BAAI/bge-small-en-v1.5

The embedding dimension is 384.

### Retrieval

For each question:

1. Generate an embedding for the question.
2. Compare it with stored transcript embeddings.
3. Rank chunks using cosine similarity.
4. Select the highest-ranked chunks.
5. Pass the evidence to the Growth Agent.


## 7. Grounding Design

The Growth Agent receives retrieved transcript material as explicit evidence.

The agent is instructed to:

- Use the supplied transcript evidence.
- Avoid unsupported outside knowledge.
- Identify relevant sources.
- Preserve conversational context.
- Acknowledge when the evidence is insufficient.

This makes retrieval a required part of the answer-generation process.


## 8. Source Traceability

Each retrieved transcript chunk contains source information.

The assistant stores the source trace with the generated chat message.

The frontend exposes those sources through the Source Panel.

The flow is:

User Question
    |
    v
Retrieved Transcript Chunk
    |
    v
Agent Answer
    |
    v
Source Reference

This allows users to trace an answer back to the transcript material used.


## 9. LLM Provider Design

The LLM layer is separated from the API and retrieval layers.

Supported providers:

- Ollama
- Anthropic

The provider is selected through environment configuration.

Example:

MODEL_PROVIDER=ollama
OLLAMA_MODEL=llama3.2:3b
OLLAMA_BASE_URL=http://localhost:11434

Ollama is the default provider for the local demo.

Anthropic can be enabled by supplying the required API key and model
configuration.


## 10. Growth Agent

The Growth Agent is responsible for producing grounded conversational
responses.

Its main responsibilities are:

1. Receive the user's question.
2. Receive relevant transcript evidence.
3. Apply grounding instructions.
4. Generate the final response.
5. Include source references.
6. Avoid presenting unsupported information as transcript-derived fact.


## 11. Ship 30 for 30 Skill

The application contains a dedicated Ship 30 for 30 writing skill.

The skill uses transcript evidence and applies writing principles such as:

- Strong opening hook
- Clear narrative
- Short paragraphs
- Headings
- Skimmable formatting
- Practical takeaways
- Grounded claims

The skill is separate from normal conversational question answering so that
long-form writing has its own instructions and output structure.


## 12. Artifact Design

The assistant can generate written or visual artifacts.

The Artifact Viewer appears inside the application instead of redirecting the
user to another page.

The viewer supports:

- Preview
- Code

Generated HTML is supplied to the preview using srcDoc.


## 13. Artifact Security

Generated HTML is treated as untrusted content.

The backend removes potentially executable:

- script elements
- inline event-handler attributes

The frontend renders generated HTML inside a sandboxed iframe.

The sandbox creates a boundary between generated content and the main
application.

This reduces the risk of generated HTML executing JavaScript with access to
the parent application.


## 14. Error Handling

The API uses structured errors.

Example:

{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request contains invalid or missing fields."
  }
}

The system handles failures including:

- Invalid requests
- Missing sessions
- Retrieval failures
- Unavailable Ollama
- Missing Anthropic credentials
- Model timeouts
- Unexpected server errors

Internal stack traces are logged by the backend but are not returned to the
user.


## 15. Operational Design

The application uses environment variables for configuration.

Secrets are not committed to the repository.

An .env.example file documents the required configuration.

The system provides a health endpoint that reports application, database,
and model provider status.

Docker Compose is provided for running the application components together.


## 16. Key Tradeoffs

### Local Model vs Cloud Model

Ollama provides a local and reproducible demo environment without requiring an
external model API.

The tradeoff is that local generation can have higher latency and lower
generation quality depending on available hardware.

Anthropic provides an alternative cloud configuration when stronger model
performance is required.


### Strict Grounding vs General Knowledge

Strict transcript grounding improves source traceability and reduces
unsupported claims.

The tradeoff is that the assistant may not answer questions when the
available transcripts do not contain enough information.


### Retrieval Size

Too few chunks can omit relevant information.

Too many chunks increase prompt size, latency, and model processing cost.

The current design retrieves a small set of high-similarity chunks.


### Sandboxed Rendering

Sandboxing limits the capabilities of generated HTML.

The tradeoff is that some advanced interactive behavior may not work inside
the restricted environment.


## 17. Future Improvements

Potential future improvements include:

- Hybrid keyword and vector retrieval
- Retrieval reranking
- Streaming model responses
- Stronger HTML sanitization
- Automated grounding evaluation
- Transcript refresh jobs
- Authentication
- Richer source metadata
- Production monitoring and observability