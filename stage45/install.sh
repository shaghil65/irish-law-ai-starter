#!/usr/bin/env bash
set -euo pipefail
if [[ ! -f docker-compose.yml || ! -f backend/app/main.py || ! -f frontend/app/page.tsx ]]; then
 echo 'Run from the irish-law-ai-starter project root.' >&2; exit 1
fi
stamp=$(date +%Y%m%d-%H%M%S)
backup="stage45-backup-$stamp"; mkdir -p "$backup"
cp backend/app/main.py "$backup/main.py"
cp backend/requirements.txt "$backup/requirements.txt"
cp frontend/app/page.tsx "$backup/page.tsx"
cp frontend/app/globals.css "$backup/globals.css"
[[ ! -f backend/app/research.py ]] || cp backend/app/research.py "$backup/research.py"
cp stage45/backend/app/research.py backend/app/research.py
cp stage45/backend/app/index_embeddings.py backend/app/index_embeddings.py
cp stage45/frontend/app/page.tsx frontend/app/page.tsx
cp stage45/frontend/app/stage45.css frontend/app/stage45.css
python3 - <<'PY'
from pathlib import Path
p=Path('backend/app/main.py'); s=p.read_text()
line='from app.research import router as research_router\napp.include_router(research_router)'
if 'app.include_router(research_router)' not in s: s+='\n\n# Stages 4-5 hybrid retrieval and grounded answers\n'+line+'\n'
p.write_text(s)
p=Path('backend/requirements.txt'); s=p.read_text()
if not any(x.strip().startswith('openai') for x in s.splitlines()): s+='\nopenai>=1.50,<3\n'
p.write_text(s)
p=Path('frontend/app/globals.css'); s=p.read_text()
if '@import "./stage45.css";' not in s: s='@import "./stage45.css";\n'+s
p.write_text(s)
PY
# Add API key to backend without changing existing docker-compose.yml or storing key in browser.
cat > docker-compose.stage45.yml <<'YAML'
services:
  backend:
    environment:
      OPENAI_API_KEY: ${OPENAI_API_KEY:-}
      OPENAI_CHAT_MODEL: ${OPENAI_CHAT_MODEL:-gpt-4.1-mini}
  ingest:
    environment:
      OPENAI_API_KEY: ${OPENAI_API_KEY:-}
YAML
# indexer uses backend service; ingest remains untouched.
echo "Installed combined search/AI upgrade. Backup: $backup"
echo 'Use: docker compose -f docker-compose.yml -f docker-compose.stage45.yml up -d --build backend frontend'
