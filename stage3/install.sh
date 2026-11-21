#!/usr/bin/env bash
set -euo pipefail
if [[ ! -f docker-compose.yml || ! -f backend/app/main.py || ! -f frontend/app/page.tsx ]]; then
  echo 'ERROR: Run from the irish-law-ai-starter project root.' >&2; exit 1
fi
mkdir -p stage3-backup
cp backend/app/main.py stage3-backup/main.py
cp frontend/app/page.tsx stage3-backup/page.tsx
cp frontend/app/globals.css stage3-backup/globals.css
cp backend/app/search.py stage3-backup/search.py 2>/dev/null || true
cp stage3/backend/app/search.py backend/app/search.py
cp stage3/frontend/app/page.tsx frontend/app/page.tsx
cp stage3/frontend/app/stage3.css frontend/app/stage3.css
python3 - <<'PY'
from pathlib import Path
p=Path('backend/app/main.py'); s=p.read_text()
if 'from app.search import router as search_router' not in s:
    s += '\n\n# Stage 3 keyword search\nfrom app.search import router as search_router\napp.include_router(search_router)\n'
p.write_text(s)
p=Path('frontend/app/globals.css'); s=p.read_text()
if '@import "./stage3.css";' not in s:
    s = '@import "./stage3.css";\n' + s
p.write_text(s)
PY
printf '\nInstalled Stage 3 keyword search. Backups: stage3-backup/\n'
printf 'Run: docker compose up -d --build backend frontend\n'
