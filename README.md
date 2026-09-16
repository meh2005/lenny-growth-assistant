# The Lenny Growth Assistant

A full-stack AI conversational assistant grounded in Lenny's Podcast transcripts. It helps product and growth teams explore ideas from Lenny's Podcast, generate grounded written content, and create rendered HTML artifacts directly in the app.

## Features

- Grounded Q&A using Lenny's Podcast transcript knowledge base
- RAG pipeline with PostgreSQL + pgvector
- Semantic retrieval using BAAI/bge-small-en-v1.5 embeddings
- Persistent independent chat sessions
- Source traceability for retrieved transcript passages
- Ollama support for local LLM inference
- Anthropic support as a configurable cloud provider
- Dedicated Ship 30 for 30 writing skill
- Markdown/content generation
- HTML artifact generation with an in-app Artifact Viewer
- Sandboxed rendering of generated HTML
- FastAPI backend
- React frontend
- PostgreSQL persistence
- Structured API errors and health checks
- Automated tests for validation, RAG helpers, and agent grounding
- Docker Compose configuration for the application stack

## Architecture

```text
React Frontend
      |
      v
FastAPI Backend
      |
      +---- Chat Sessions
      |
      +---- Growth Agent
      |        |
      |        +---- RAG Retriever
      |        |       |
      |        |       v
      |        |   PostgreSQL + pgvector
      |        |
      |        +---- Ollama / Anthropic
      |
      +---- Ship 30 Skill
      |
      +---- Artifact Generation
               |
               v
        Sandboxed Artifact Viewer
```

## Tech Stack

### Frontend
- React
- Vite
- React Router
- Axios
- React Markdown
- Tailwind CSS
- Leaflet

### Backend
- Python
- FastAPI
- SQLAlchemy
- Pydantic
- httpx

### AI / RAG
- Ollama
- Anthropic
- FastEmbed
- BAAI/bge-small-en-v1.5
- pgvector

### Database
- PostgreSQL
- pgvector

### Infrastructure
- Docker
- Docker Compose
- Nginx

## Knowledge Base

The knowledge base is built from Lenny's Podcast transcripts.

The transcripts are chunked into overlapping passages and embedded using `BAAI/bge-small-en-v1.5`. Embeddings are stored in PostgreSQL using pgvector.

At query time:

1. The user's question is embedded.
2. The most semantically relevant transcript chunks are retrieved.
3. Retrieved evidence is provided to the Growth Agent.
4. The agent is instructed to answer only from the supplied transcript evidence.
5. Relevant sources are returned with the response.

If the retrieved material does not support an answer, the assistant is instructed to acknowledge the limitation instead of presenting unsupported information as fact.

## Local Setup

### Requirements

- Python 3.12+
- Node.js
- npm
- PostgreSQL with pgvector, or Docker
- Ollama

### 1. Clone the repository

```bash
git clone https://github.com/meh2005/lenny-growth-assistant.git
cd lenny-growth-assistant
```

### 2. Configure the backend

```bash
cd backend
python -m venv venv
```

Windows:

```powershell
.\venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create `.env` from the example:

```powershell
Copy-Item .env.example .env
```

Configure the database and model provider in `.env`.

For local Ollama:

```env
MODEL_PROVIDER=ollama
OLLAMA_MODEL=llama3.2:3b
OLLAMA_BASE_URL=http://localhost:11434
```

### 3. Start Ollama

Install Ollama and make sure it is running.

Pull the model:

```bash
ollama pull llama3.2:3b
```

### 4. Start PostgreSQL

The repository includes a PostgreSQL + pgvector Docker configuration.

From the project root:

```bash
docker compose up -d postgres
```

### 5. Ingest transcripts

From `backend`:

```bash
python scripts/ingest_transcripts.py
```

This creates the transcript chunks and embeddings in PostgreSQL.

### 6. Start the backend

From `backend`:

```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at:

```text
http://localhost:8000
```

Health check:

```text
http://localhost:8000/health
```

### 7. Start the frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

## Docker

The project includes Dockerfiles for the backend and frontend and a Docker Compose configuration containing:

- PostgreSQL + pgvector
- FastAPI backend
- React frontend served through Nginx

```bash
docker compose up --build
```

The frontend is exposed on port `5173` and the backend on port `8000`.

For local Ollama inference, the backend is configured to reach the host Ollama service through:

```text
http://host.docker.internal:11434
```

## LLM Providers

The application supports two provider modes:

### Ollama

Used for the local/demo configuration.

```env
MODEL_PROVIDER=ollama
OLLAMA_MODEL=llama3.2:3b
OLLAMA_BASE_URL=http://localhost:11434
```

### Anthropic

Can be enabled by configuring:

```env
MODEL_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_key
ANTHROPIC_MODEL=claude-sonnet-4-5
```

The active provider is visible in the application UI.

## API

### Health

```http
GET /health
```

Returns application, database, and provider health information.

### Sessions

```http
POST /sessions
GET /sessions
DELETE /sessions/{session_id}
```

### Chat

```http
POST /chat
```

Chat requests include a session ID so conversation context can persist across messages.

## Grounding and Safety

The Growth Agent is designed to operate only on retrieved transcript evidence.

The application:

- Separates retrieval from generation.
- Passes retrieved transcript evidence explicitly to the agent.
- Includes source identifiers with generated answers.
- Instructs the model not to rely on outside knowledge.
- Acknowledges when the transcript material is insufficient.
- Sanitizes generated HTML before rendering.
- Uses a sandboxed iframe for artifact rendering.

Generated HTML is treated as untrusted content and is not executed directly in the main application context.

## Ship 30 for 30

The application includes a dedicated Ship 30 for 30 writing skill.

The skill uses retrieved transcript evidence and writing principles to produce useful, skimmable written content with:

- A strong opening hook
- Clear narrative structure
- Short paragraphs
- Headings and lists
- Practical takeaways
- Transcript source references
- Grounding constraints

## Testing

Run the backend tests with:

```bash
python -m pytest
```

The test suite covers:

- Request validation
- RAG helper behavior
- Agent grounding and evidence passing

## Project Documentation

Additional project documentation is available in:

- `docs/PRD.md` — product requirements and scope
- `docs/design.md` — UX and system design
- `docs/architecture.md` — technical architecture
- `agent-transcripts/implementation-log.md` — AI-assisted implementation process, failures, corrections, and verification

## Repository Structure

```text
lenny-growth-assistant/
├── agent-transcripts/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── rag/
│   │   └── services/
│   └── scripts/
├── data/
│   └── transcripts/
├── docs/
├── frontend/
│   └── src/
├── tests/
├── docker-compose.yml
└── README.md
```

## Configuration

Never commit secrets.

Use `.env` locally and keep credentials out of version control. `.env.example` is provided as the configuration template.

## Status

The project includes the core conversational assistant, transcript RAG pipeline, persistent sessions, local Ollama support, Anthropic provider support, Ship 30 writing skill, artifact viewer, source traceability, structured errors, health checks, Docker configuration, and automated tests.