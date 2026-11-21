# Irish Law AI — Combined Stages 3, 4 and 5

Preserves the existing `legislation_documents` and `legislation_provisions` tables. Does **not** run `docker compose down -v` or reimport data. Installer backs up modified files.

## 1. Install

Save ZIP in `~/Downloads/Projects`, then from Terminal:

```bash
cd ~/Downloads/Projects/irish-law-ai-starter
unzip -o ~/Downloads/Projects/irish-law-ai-stages3-4-5-combined.zip -d .
bash stage45/install.sh
docker compose -f docker-compose.yml -f docker-compose.stage45.yml up -d --build backend frontend
```

Keyword search works immediately at http://localhost:3000 and `http://localhost:8000/api/research/search?q=court&mode=keyword`.

## 2. Enable semantic search and AI answers (optional; paid API usage)

Create or edit `.env` in project root. Add your own API key (do not share it in chat or commit it):

```dotenv
OPENAI_API_KEY=your_api_key_here
OPENAI_CHAT_MODEL=gpt-4.1-mini
```

An OpenAI API key with billing access is needed; a ChatGPT subscription alone is not an API key. The application sends query text and imported legislation excerpts to OpenAI for embeddings/answers. Confirm this is appropriate for your data. Do not enter confidential client facts.

Restart backend with environment loaded:

```bash
docker compose -f docker-compose.yml -f docker-compose.stage45.yml up -d --build backend
```

Index all existing provisions (API charges apply, may take several minutes):

```bash
docker compose -f docker-compose.yml -f docker-compose.stage45.yml exec backend python -m app.index_embeddings
```

Indexing creates `legislation_embeddings` and an HNSW pgvector index, and is resumable. It **does not** modify the existing legislation tables. For a cheap trial, use `--max-items 30` first; rerun without the flag to complete. Partial indexing means semantic results cover only indexed provisions.

Test:

```bash
curl -i 'http://localhost:8000/api/research/search?q=family%20court&mode=hybrid&limit=5'
curl -i -X POST 'http://localhost:8000/api/research/ask' -H 'Content-Type: application/json' -d '{"question":"What does the imported legislation say about family courts?","mode":"hybrid"}'
```

## Limits and safety

- Keyword mode works without OpenAI key. Semantic and hybrid modes require key **and** completed indexing. AI answers require key.
- Results cover **imported enacted Acts**, not necessarily consolidated or commenced law. Verify amendments, repeal, commencement and official source before relying on any answer.
- The AI receives only excerpts (up to 900 characters each), so complex questions may be under-supported. Numbered citations link to **the Act**, not guaranteed deep links to the exact provision.
- No automated citation validation, case law, regulatory material, version reconciliation, user authentication, or rate limiting. Run locally, not as a public production legal-advice service.
- Existing Stage 3 `/api/search` is retained; new routes are `/api/research/search` and `/api/research/ask`.
- If your `.env` already contains credentials, add the key without replacing the file. Keep `.env` out of version control.
