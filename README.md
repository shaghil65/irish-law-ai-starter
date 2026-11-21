# Irish Law AI

**Find the provision. Understand the law.**

Irish Law AI is an open-source-style, local-first legal research application for exploring Irish legislation. It combines full-text and semantic search with AI-assisted answers and supporting references to the [Irish Statute Book](https://www.irishstatutebook.ie/). The AI runs locally through Ollama, with no paid AI API required.

## Features

- **Modern research interface** — responsive Next.js UI with suggested questions and source cards.
- **Keyword search** — PostgreSQL full-text search; works without an AI model.
- **Semantic search** — meaning-based retrieval with locally generated embeddings.
- **Hybrid search** — combines keyword and semantic rankings.
- **AI-assisted research** — Ollama generates answers from retrieved legislative provisions.
- **Source transparency** — view supporting excerpts and links to official legislation.
- **Year filtering** — narrow results by Act year.

## Tech stack

| Component | Technology |
| --- | --- |
| Frontend | Next.js, React, TypeScript |
| Backend | FastAPI, Python |
| Database | PostgreSQL |
| Vector search | pgvector |
| Local AI | Ollama (`llama3.2:3b`) |
| Embeddings | Ollama (`nomic-embed-text`) |
| Development environment | Docker Compose |

## Getting started

### Prerequisites

- Docker Desktop with Docker Compose
- [Ollama](https://ollama.com/) installed on your computer
- Git

The commands below reflect the current macOS development configuration.

### 1. Configure the project

```bash
cp -n .env.example .env
```

Set the required environment variables according to `.env.example`. Keep `.env` out of version control.

### 2. Start Ollama and download the models

On macOS, install Ollama if needed:

```bash
brew install ollama
```

Start Ollama (unless it is already running):

```bash
ollama serve
```

In a separate terminal:

```bash
ollama pull llama3.2:3b
ollama pull nomic-embed-text
ollama list
```

### 3. Start the application

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.free.yml \
  -f docker-compose.portfix.yml \
  -f docker-compose.backendfix.yml \
  -f docker-compose.frontendfix.yml \
  up -d --build db backend frontend
```

Open **http://localhost:3001**.

The additional Compose files reflect local port adjustments: the database and backend communicate inside Docker, while the frontend is available on port `3001`.

### 4. Index legislation for semantic search

Once legislation has been imported and Ollama is running:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.free.yml \
  -f docker-compose.portfix.yml \
  -f docker-compose.backendfix.yml \
  -f docker-compose.frontendfix.yml \
  exec backend python -m app.index_local_embeddings
```

Indexing time depends on the number of provisions and the machine running Ollama. Keyword search does not require embeddings.

## Search modes

| Mode | How it works | Requires Ollama? |
| --- | --- | --- |
| Keyword | PostgreSQL full-text matching | No |
| Semantic | Vector similarity over indexed provisions | Yes |
| Hybrid | Combines keyword and semantic retrieval | Yes |

The research assistant uses retrieved provisions as context for its responses. The source cards make it easier to check the underlying legislation.

## API

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/search` | Basic keyword search |
| `GET` | `/api/research/search` | Keyword, semantic or hybrid search |
| `POST` | `/api/research/ask` | AI-assisted research with sources |

Example request from within the backend container or its Docker network:

```bash
curl 'http://localhost:8000/api/research/search?q=employment&mode=keyword&limit=5'
```

## Repository layout

```text
irish-law-ai-starter/
├── backend/
│   ├── app/                 # FastAPI routes, retrieval and AI research
│   ├── ingest/              # Legislation ingestion tools
│   └── tests/
├── frontend/
│   └── app/                 # Next.js application and styles
├── database/
│   └── init/                # Database initialization
├── data/                    # Local legislation inputs and reports
├── docker-compose.yml
├── docker-compose.free.yml
├── docker-compose.portfix.yml
├── docker-compose.backendfix.yml
├── docker-compose.frontendfix.yml
├── .env.example
└── README.md
```

## Development status

The application currently supports a working local web interface, legislation search, Ollama-based research responses and source evidence cards. At the last reported checkpoint, the development database contained **49 imported Acts and 3,496 provisions**; this is a snapshot, not a complete collection of Irish law.

Planned improvements include expanding coverage to principal Acts, improving retrieval and relevance checks, more precise section links, automated evaluation, and simplifying the Docker configuration.

## Useful commands

Check running containers:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.free.yml \
  -f docker-compose.portfix.yml \
  -f docker-compose.backendfix.yml \
  -f docker-compose.frontendfix.yml \
  ps
```

Check Ollama:

```bash
curl http://localhost:11434/api/tags
```

Stop containers without removing database volumes:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.free.yml \
  -f docker-compose.portfix.yml \
  -f docker-compose.backendfix.yml \
  -f docker-compose.frontendfix.yml \
  stop
```

## Legal information note

Irish Law AI is a research tool, not legal advice. Its corpus is incomplete, and retrieved provisions or AI-generated answers may be inaccurate or out of date. Verify the current law against the [Irish Statute Book](https://www.irishstatutebook.ie/).

---

**Irish Law AI** · Local-first Irish legislation research
