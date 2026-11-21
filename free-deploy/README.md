# Irish Law AI — free local AI + public deployment

This is a patch for the EXISTING Irish Law AI project, not a replacement database. It uses your imported Acts. No OpenAI API key, subscription or paid AI inference is required.

## Requirements
- Mac with Docker Desktop, Homebrew, Python 3 and enough memory to run a small LLM
- Existing project with working keyword search and imported legislation
- Internet connection for installation and public access

## 1. Install the patch (run in the project root)

```bash
cd ~/Downloads/Projects/irish-law-ai-starter
unzip -o ~/Downloads/Projects/irish-law-ai-free-deploy.zip -d .
bash free-deploy/install.sh
```

The installer saves replaced files to `free-deploy-backup-<timestamp>`. It does not drop or recreate the database. Do not use `docker compose down -v`.

## 2. Run Ollama directly on your Mac (Metal acceleration on Apple Silicon)

```bash
brew install ollama
ollama serve
```

Keep `ollama serve` running in a separate terminal. In another terminal:

```bash
ollama pull nomic-embed-text
ollama pull llama3.2:3b
```

If the Ollama desktop app already runs the server, you do not need a second `ollama serve` process. Model downloads take disk space; speed depends on your Mac.

## 3. Launch Docker

```bash
cd ~/Downloads/Projects/irish-law-ai-starter
docker compose -f docker-compose.yml -f docker-compose.free.yml up -d --build db backend frontend
```

Test: http://localhost:3000 . Keyword mode works without embeddings.

## 4. Index the legislation locally (once, or after new imports)

```bash
docker compose -f docker-compose.yml -f docker-compose.free.yml exec backend python -m app.index_local_embeddings
```

Indexing 3,496 provisions can take a while. It resumes and skips already indexed records. Afterward choose **Hybrid** or **Semantic** and use **Ask AI with citations**.

If the indexer cannot reach Ollama, ensure the Mac's Ollama service is reachable from Docker Desktop at `http://host.docker.internal:11434`. Ollama may bind only to localhost; for Docker access restart it on the host with `OLLAMA_HOST=0.0.0.0:11434 ollama serve`. **Do not port-forward port 11434 or expose it publicly**. Restrict access using the Mac firewall and trusted local network.

## 5. Publish a free temporary public URL

```bash
brew install cloudflared
cloudflared tunnel --url http://localhost:3000
```

Cloudflared prints a temporary `https://...trycloudflare.com` URL. Share that URL to test the site. Keep your Mac, Docker, Ollama and cloudflared running. A Quick Tunnel URL is temporary and may change; this is a testing/demo deployment, not guaranteed production hosting. No purchased domain is required.

## Security before sharing publicly

- **Do not publish a public AI service without rate limiting and authentication.** This patch is a deployment demo, not hardened production infrastructure. Unknown visitors can consume your Mac's compute resources.
- Your original compose file may use default database credentials. Set strong credentials in `.env` and ensure the existing database password and `DATABASE_URL` match. Do not reset a populated database blindly.
- Backend and PostgreSQL ports are bound to `127.0.0.1` by the override; the tunnel exposes only the frontend.
- Keep Docker Desktop, Next.js, FastAPI, Ollama and the Mac updated. Monitor logs and resource use.
- This corpus contains enacted Acts and may not reflect amendments, repeals or commencement. Verify every answer against official current legislation.

## Troubleshooting

```bash
docker compose -f docker-compose.yml -f docker-compose.free.yml logs --tail=100 backend frontend
curl http://localhost:3000/api/research/search?q=court
curl http://localhost:11434/api/tags
```

If `frontend/app/page.tsx` was customized, compare the backup before making further changes. If a previous Stage 4/5 OpenAI patch was installed, this patch replaces its research router with local-only code. The old OpenAI package may remain installed but is not called by the new endpoints.

## Running costs

No required paid API or hosting subscription for this configuration. You supply the Mac, power, disk space, and internet access. Cloudflare Quick Tunnels have service limitations and are not a permanent uptime guarantee.
