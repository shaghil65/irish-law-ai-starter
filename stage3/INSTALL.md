# Stage 3: Irish legal keyword search

This patch adds a real PostgreSQL full-text search API and Next.js results interface to the Stage 1/2/2.5 starter. It uses the existing `legislation_provisions.search_vector` and its GIN index. **It does not implement embeddings, semantic search or AI-generated answers.**

## Installation (Mac)

1. Place `irish-law-ai-stage3-keyword.zip` inside `~/Downloads/Projects`.
2. In Terminal:

```bash
cd ~/Downloads/Projects/irish-law-ai-starter
unzip -o ~/Downloads/Projects/irish-law-ai-stage3-keyword.zip -d .
bash stage3/install.sh
docker compose up -d --build backend frontend
```

3. Test the API:

```bash
curl -G --data-urlencode 'q=court' 'http://localhost:8000/api/search'
```

4. Open `http://localhost:3000` and search.

## Safety and limitations

- Existing database records and volumes are not changed; **never use `docker compose down -v`**.
- Existing `backend/app/main.py`, `frontend/app/page.tsx`, and `frontend/app/globals.css` are backed up to `stage3-backup/`.
- Results are from imported enacted Acts, not necessarily current consolidated law. Source links open the official enacted Act, not necessarily the specific section.
- Only English full-text matching is supported. Semantic embeddings and AI-generated answers require separate implementation.
- The first 25 results are shown in the UI (API supports up to 50). No pagination yet.
- For local development only; add authentication, rate limiting and production configuration before public deployment.

## Troubleshooting

Check `docker compose logs --tail=80 backend frontend` if either service fails. Verify the imported data with `docker compose exec db psql -U lawai -d irish_law -c 'SELECT COUNT(*) FROM legislation_provisions;'`.
