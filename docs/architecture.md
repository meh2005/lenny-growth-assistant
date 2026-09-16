# Architecture Document

## 1. System Overview

The Lenny Growth Assistant is a full-stack application composed of four main
layers:

1. React frontend
2. FastAPI backend
3. Agent and RAG layer
4. PostgreSQL with pgvector

The LLM provider is configurable between local Ollama and Anthropic.

---

## 2. High-Level Architecture

```text
                         User
                          |
                          v
                 React Frontend
                          |
                    HTTP / JSON
                          |
                          v
                  FastAPI Backend
                          |
             +------------+------------+
             |            |            |
             v            v            v
          Sessions      Chat        Health
             |            |
             |            v
             |       Growth Agent
             |            |
             |            v
             |       RAG Retriever
             |            |
             |            v
             |    PostgreSQL + pgvector
             |            |
             |            v
             |   Transcript Chunks
             |
             v
        PostgreSQL Database

                     Growth Agent
                          |
                          v
                   LLM Provider
                    /          \
                   /            \
               Ollama        Anthropic
## 3. Frontend

The frontend is built with React and Vite.

Main responsibilities:

- Display conversations
- Create and manage sessions
- Send chat requests to the backend
- Display Markdown responses
- Display transcript sources
- Display generated artifacts

Main components:

- App
- Sidebar
- Chat
- Message
- SourcePanel
- ArtifactViewer

The frontend communicates with the backend using HTTP requests.


## 4. Backend

The backend is built with FastAPI.

Main API areas:

- /api/health
- /api/sessions
- /api/chat

The backend is responsible for:

- Request validation
- Session management
- Message persistence
- Transcript retrieval
- Agent execution
- Source tracking
- LLM provider selection
- Error handling


## 5. Database

PostgreSQL is used for application persistence.

The database contains three main tables.

### chat_sessions

Stores conversation sessions.

Important fields:

- id
- title
- created_at

### chat_messages

Stores messages belonging to sessions.

Important fields:

- id
- session_id
- role
- content
- sources
- created_at

### transcript_chunks

Stores the podcast transcript knowledge base.

Important fields:

- id
- episode
- source_id
- content
- embedding

The embedding column uses pgvector.


## 6. Transcript Ingestion

The transcript ingestion pipeline is:

Transcript files
    |
    v
Text extraction
    |
    v
Chunking
    |
    v
Embedding generation
    |
    v
PostgreSQL + pgvector

The current knowledge base contains approximately:

- 303 episodes
- 4,733 transcript chunks

Chunk configuration:

- Chunk size: 1200 characters
- Overlap: 200 characters

The embedding model is:

BAAI/bge-small-en-v1.5

The embedding dimension is 384.


## 7. Retrieval

When a user sends a question:

1. The question is converted into an embedding.
2. The embedding is compared with stored transcript embeddings.
3. The closest transcript chunks are retrieved.
4. The retrieved chunks are passed to the Growth Agent.
5. The agent generates a grounded response.

Cosine distance is used for vector similarity retrieval.


## 8. Growth Agent

The Growth Agent is responsible for generating grounded conversational
responses.

It receives:

- User question
- Conversation context
- Retrieved transcript evidence

The agent is instructed to:

- Use the supplied transcript evidence.
- Avoid unsupported outside knowledge.
- Include relevant source references.
- Preserve conversation context.
- Acknowledge when the evidence is insufficient.

This keeps the assistant focused on the transcript knowledge base.


## 9. LLM Provider

The LLM layer is separated from the rest of the application.

Supported providers:

- Ollama
- Anthropic

The provider is selected through environment variables.

For Ollama:

MODEL_PROVIDER=ollama
OLLAMA_MODEL=llama3.2:3b
OLLAMA_BASE_URL=http://localhost:11434

Ollama is the default provider for the local demonstration.

Anthropic can be enabled by providing an API key and model configuration.


## 10. Conversation Context

Each conversation has a unique session ID.

Messages are associated with their session.

This prevents conversations from being mixed together.

Follow-up questions use the same session so previous messages can be used as
context along with newly retrieved transcript evidence.


## 11. Source Traceability

Retrieved transcript chunks contain source information.

The source information is stored with the assistant message.

The frontend displays this information through the Source Panel.

The source flow is:

User question
    |
    v
Retrieved transcript
    |
    v
Agent response
    |
    v
Source reference

This allows users to understand which transcript material was used.


## 12. Ship 30 for 30 Skill

The application includes a dedicated Ship 30 for 30 writing skill.

The skill uses transcript evidence and applies writing principles including:

- Strong opening hook
- Clear narrative
- Short paragraphs
- Skimmable formatting
- Useful takeaways
- Grounded claims

The writing skill is separated from normal question answering so that
long-form content has its own instructions and output structure.


## 13. Artifact Generation

The application supports generated Markdown and HTML artifacts.

The Artifact Viewer is displayed beside the chat.

It provides:

- Preview
- Code view

The generated HTML is passed to the viewer rather than opening a separate
page.


## 14. Artifact Security

Generated HTML is treated as untrusted content.

The backend removes potentially executable content such as:

- Script elements
- Inline event-handler attributes

The frontend renders generated HTML inside a sandboxed iframe.

This provides a separation between generated content and the main React
application.


## 15. Error Handling

The backend uses structured API errors.

Example:

{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request contains invalid or missing fields."
  }
}

The system handles:

- Invalid requests
- Missing sessions
- Retrieval failures
- Ollama unavailable
- Missing Anthropic credentials
- Model timeouts
- Unexpected server errors

Detailed exceptions are logged on the server.

Internal stack traces are not returned to the user.


## 16. Health Monitoring

The application provides a health endpoint.

The endpoint reports:

- Application status
- Configured model provider
- Configured model
- Database status

This provides a simple way to verify that the main backend dependencies are
available.


## 17. Docker Architecture

Docker Compose defines three main services:

- PostgreSQL
- Backend
- Frontend

The PostgreSQL service uses a pgvector-enabled image.

The backend runs using Uvicorn.

The frontend is built with Vite and served using Nginx.


## 18. Configuration

Application configuration is supplied through environment variables.

Important variables include:

DATABASE_URL
MODEL_PROVIDER
OLLAMA_MODEL
OLLAMA_BASE_URL
ANTHROPIC_API_KEY
ANTHROPIC_MODEL

Secrets are not committed to the repository.

The repository contains an .env.example file showing the required
configuration.


## 19. Failure Handling

The system is designed to handle common operational failures.

### Ollama unavailable

The backend returns a clear error indicating that the local model is
unavailable.

### Model timeout

A timeout is converted into a user-readable error.

### Retrieval failure

The backend returns a retrieval error rather than fabricating transcript
evidence.

### Invalid request

FastAPI validation returns a structured validation error.

### Missing session

The API returns a SESSION_NOT_FOUND error.

### Unexpected exception

The exception is logged and the API returns an INTERNAL_ERROR response.


## 20. Technology Stack

| Layer | Technology |
| --- | --- |
| Frontend | React + Vite |
| Styling | Tailwind CSS |
| Backend | FastAPI |
| Language | Python |
| Database | PostgreSQL |
| Vector Search | pgvector |
| Embeddings | FastEmbed |
| Local LLM | Ollama |
| Cloud LLM | Anthropic |
| ORM | SQLAlchemy |
| Frontend Server | Nginx |
| Containers | Docker Compose |
| Testing | Pytest |


## 21. Main Design Tradeoffs

### Local Model

Ollama provides a local and reproducible demonstration environment.

The tradeoff is that local inference can have higher latency and lower
generation quality depending on available hardware.

### Cloud Model

Anthropic provides an alternative provider when cloud inference is preferred.

The tradeoffs are API dependency, credentials, and usage cost.

### Strict Grounding

Strict transcript grounding reduces unsupported claims and improves source
traceability.

The tradeoff is that the assistant may not be able to answer questions when
the transcript knowledge base does not contain enough information.

### Retrieval Size

Retrieving too few chunks can miss useful context.

Retrieving too many chunks increases prompt size and model latency.

The current design therefore retrieves a limited number of relevant chunks.

### Sandboxed Artifacts

Sandboxed rendering improves isolation of generated HTML.

The tradeoff is that some advanced browser functionality may not work inside
the restricted environment.


## 22. Future Improvements

Potential improvements include:

- Hybrid keyword and vector retrieval
- Retrieval reranking
- Streaming responses
- Stronger HTML sanitization
- Automated grounding evaluation
- Automatic transcript refresh
- Authentication
- Richer source metadata
- Production monitoring