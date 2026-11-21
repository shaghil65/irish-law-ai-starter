# Irish Law AI

**Find the provision. Understand the law.**

Irish Law AI is a local-first research preview for searching imported Irish legislation and generating evidence-led answers. It combines a Next.js frontend, a FastAPI backend, PostgreSQL full-text search, pgvector, and locally hosted Ollama models. No paid AI API is required.

> **Important:** This is a research preview, not legal advice. The corpus is incomplete, and enacted Acts may have been amended, repealed, or not commenced. AI answers and citations can be wrong or irrelevant. Always verify the current law using the [Irish Statute Book](https://www.irishstatutebook.ie/).

## Features

- Responsive legal research interface with example questions and supporting evidence cards.
- Keyword search using PostgreSQL full-text search.
- Semantic search using locally generated embeddings.
- Hybrid search combining lexical and semantic results.
- AI-assisted answers using Ollama, with links to retrieved source legislation.
- Optional Act-year filter.

**Known limitation:** Search relevance needs further work. For example, a query about *company directors' duties* has retrieved unrelated provisions about a director of a policing authority. An AI answer is **not** reliable merely because sources are displayed alongside it.

## Stack

| Layer | Technology |
| --- | --- |
| Frontend | Next.js, React, TypeScript |
| API | Python, FastAPI |
| Database | PostgreSQL, pgvector |
| Local chat model | Ollama `llama3.2:3b` |
| Local embedding model | Ollama `nomic-embed-text` |
| Containers | Docker Compose |

## Local setup (current macOS configuration)

Install Docker Desktop and Ollama. In the project directory, create `.env` from `.env.example` **only if `.env` does not already exist**:

```bash
cp -n .env.example .env
```

Install and start the local models:

```bash
brew install ollama
ollama serve
```

Keep that terminal open if you started the server manually. In another terminal:

```bash
ollama pull llama3.2:3b
ollama pull nomic-embed-text
ollama list
```

If Ollama is already running, you do not need another `ollama serve` process.

Start the current working Docker setup:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.free.yml \
  -f docker-compose.portfix.yml \
  -f docker-compose.backendfix.yml \
  -f docker-compose.frontendfix.yml \
  up -d --build db backend frontend
```

Open **http://localhost:3001**. In this development setup the frontend is published on host port 3001; the backend and database communicate over Docker's internal network.

### Index legislation for semantic search

Once Ollama is reachable from the backend and legislation has been imported:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.free.yml \
  -f docker-compose.portfix.yml \
  -f docker-compose.backendfix.yml \
  -f docker-compose.frontendfix.yml \
  exec backend python -m app.index_local_embeddings
```

Indexing can take time on a local computer. Keyword search does not require Ollama or embeddings; semantic and hybrid modes do.

## API

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/api/search` | Keyword provision search |
| `GET` | `/api/research/search` | Keyword, semantic, or hybrid retrieval |
| `POST` | `/api/research/ask` | Local AI answer based on retrieved provisions |

Example request from inside the backend container:

```bash
python - <<'PY'
import requests
r = requests.get('http://localhost:8000/api/research/search', params={'q':'company directors','mode':'keyword','limit':5}, timeout=30)
print(r.status_code)
print(r.json())
PY
```

## Data coverage and verification

At a previously reported development checkpoint, the local database contained **49 Acts and 3,496 provisions**. This is a historical development snapshot, not a live count or comprehensive coverage of Irish law. The imported material was primarily 2024 enacted legislation; principal Acts relevant to a question may be absent.

Source links currently may lead to an Act rather than the precise provision. Always inspect the original text and check amendments, commencement, and current legal status.

**Preserve your data:** Do **not** run `docker compose down -v`; removing volumes can destroy the PostgreSQL database. Use `docker compose stop` with the same five Compose files to stop services without deleting volumes.

## Troubleshooting

**Ollama unavailable:**

```bash
ollama list
curl http://localhost:11434/api/tags
```

On Docker Desktop for Mac, the backend typically connects to the host Ollama service at `http://host.docker.internal:11434`.

**Check container status:**

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.free.yml \
  -f docker-compose.portfix.yml \
  -f docker-compose.backendfix.yml \
  -f docker-compose.frontendfix.yml \
  ps
```

**Irrelevant answers:** Inspect retrieved provisions first. Hybrid reciprocal-rank fusion does not guarantee legal relevance, and semantic distance thresholds are experimental. If the corpus lacks the relevant legislation, do not treat the answer as authoritative.

## Optional temporary public demo

A Cloudflare Quick Tunnel can expose the locally running frontend while your Mac stays online:

```bash
brew install cloudflared
cloudflared tunnel --url http://localhost:3001
```

This is a **temporary demonstration**, not production hosting. Before sharing publicly, review authentication, rate limits, abuse prevention, resource limits, and security. Do not expose the database or Ollama service directly.

## Roadmap

- Import more principal Acts and track their current legal status.
- Improve legal-topic retrieval, reranking, and evidence sufficiency checks.
- Add section-specific source links and automated legal-relevance tests.
- Consolidate the local Compose overrides.
- Add security controls before public launch.

## License

No license has yet been specified. Do not assume the repository is open-source licensed until one is added.
