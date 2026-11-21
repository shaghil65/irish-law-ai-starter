#!/usr/bin/env bash
set -euo pipefail
for file in docker-compose.yml backend/app/main.py frontend/app/page.tsx frontend/app/globals.css; do
  if [[ ! -f "$file" ]]; then echo "Missing $file — run from your project root" >&2; exit 1; fi
done
stamp=$(date +%Y%m%d-%H%M%S)
backup="free-deploy-backup-$stamp"
mkdir -p "$backup"
cp backend/app/main.py "$backup/main.py"
cp frontend/app/page.tsx "$backup/page.tsx"
cp frontend/app/globals.css "$backup/globals.css"
[[ ! -f backend/app/research.py ]] || cp backend/app/research.py "$backup/research.py"
cp free-deploy/backend/app/research.py backend/app/research.py
cp free-deploy/backend/app/index_local_embeddings.py backend/app/index_local_embeddings.py
cp free-deploy/frontend/app/page.tsx frontend/app/page.tsx
cp free-deploy/frontend/app/free-deploy.css frontend/app/free-deploy.css
cp free-deploy/docker-compose.free.yml docker-compose.free.yml
mkdir -p 'frontend/app/api/[...path]'
cp 'free-deploy/frontend/app/api/[...path]/route.ts' 'frontend/app/api/[...path]/route.ts'
python3 - <<'PY'
from pathlib import Path
p=Path('backend/app/main.py');s=p.read_text()
if 'app.include_router(research_router)' not in s:
    s+='\nfrom app.research import router as research_router\napp.include_router(research_router)\n'
p.write_text(s)
p=Path('frontend/app/globals.css');s=p.read_text()
if '@import "./free-deploy.css";' not in s:s='@import "./free-deploy.css";\n'+s
p.write_text(s)
PY
printf 'Installed. Backup: %s\nNo database data was deleted.\n' "$backup"
