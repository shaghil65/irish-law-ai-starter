# Irish Law AI — Stage 1 starter

A local development scaffold for an Irish-law research assistant. Stage 1 verifies that the web UI, FastAPI backend and PostgreSQL/pgvector database start correctly.

**Important:** This starter does not yet provide legal answers or ingest legislation. Do not rely on it for legal advice. Legal retrieval, source/version tracking, citation validation and evaluation are later stages.

## Requirements

- macOS (Apple Silicon or Intel)
- Docker Desktop
- Node.js 22 LTS (Node 20.9+ is the minimum for current Next.js releases)
- Git (optional but recommended)
- 16 GB RAM is suitable for development. We will run the language model natively on macOS in a later stage, not inside Docker.

## 1. Install prerequisites

### Homebrew (if not already installed)

Follow the official instructions: https://brew.sh/

Then:

```bash
brew update
brew install node@22 git
```

If `node` is not found after installation, follow Homebrew's suggested PATH instructions. Check:

```bash
node --version
npm --version
git --version
```

### Docker Desktop

Download the correct Mac installer (Apple silicon or Intel) from:
https://docs.docker.com/desktop/setup/install/mac-install/

Open the downloaded DMG, drag Docker to Applications, launch Docker Desktop, and accept its terms. Wait until Docker reports that it is running.

Verify:

```bash
docker version
docker compose version
docker run --rm hello-world
```

## 2. Unzip and enter the project

```bash
cd ~/Downloads
unzip irish-law-ai-starter.zip
cd irish-law-ai-starter
```

If you extracted it somewhere else, `cd` to that folder instead.

## 3. Configure environment

```bash
cp .env.example .env
```

The included values are for local development only. Change `POSTGRES_PASSWORD` before any shared or production deployment. Do not commit `.env`.

## 4. Start the application

```bash
docker compose up --build
```

First startup downloads the PostgreSQL image and installs the frontend/backend dependencies, so it may take a few minutes.

Open:

- Frontend: http://localhost:3000
- Backend API docs: http://localhost:8000/docs
- Backend health: http://localhost:8000/health
- Backend status: http://localhost:8000/api/status

The page should show that the API is reachable and that the legal corpus / answer engine are not enabled yet.

Stop the stack with `Ctrl+C`. To stop and remove containers:

```bash
docker compose down
```

To also delete the local database volume (this permanently deletes local database data):

```bash
docker compose down -v
```

## 5. Check the database

```bash
docker compose exec db psql -U lawai -d irish_law -c '\dx'
```

You should see `vector` in the installed extensions list. The initial schema is in `database/init/001_schema.sql`.

## 6. Useful development commands

```bash
# Follow all service logs
docker compose logs -f

# Follow one service
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f db

# Restart after changing Docker configuration
docker compose up --build

# Check containers
docker compose ps
```

The frontend and backend source folders are mounted into their containers for live development.

## Project layout

```text
irish-law-ai/
├── backend/
│   ├── app/
│   │   └── main.py
│   ├── Dockerfile
│   └── requirements.txt
├── database/
│   └── init/
│       └── 001_schema.sql
├── frontend/
│   ├── app/
│   │   ├── globals.css
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── Dockerfile
│   └── package.json
├── .env.example
├── .gitignore
└── docker-compose.yml
```

## Next stages

1. Import and parse official Irish legislation, preserving official identifiers, source URLs, dates and amendment/revision status.
2. Add ingestion validation and a source/version model.
3. Add hybrid lexical + vector retrieval and reranking.
4. Connect a locally hosted model (Ollama) only after retrieval is working.
5. Require answers to cite retrieved provisions; validate every citation against the stored source.
6. Build an evaluation set with Irish legal questions and have qualified reviewers assess accuracy.

Never treat a section's existence as proof that its wording is current or applicable. The production system must distinguish enacted text, revised text, commencement, amendments and repeals.
