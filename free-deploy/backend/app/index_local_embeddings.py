"""Idempotent local Ollama embedding indexer. No external AI APIs."""
import os
import time
import json
import urllib.request
import psycopg
from psycopg.rows import dict_row

URL = os.getenv('OLLAMA_URL', 'http://host.docker.internal:11434').rstrip('/')
MODEL = os.getenv('OLLAMA_EMBED_MODEL', 'nomic-embed-text')

def embed(texts):
    body = json.dumps({'model': MODEL, 'input': texts, 'truncate': True}).encode()
    req = urllib.request.Request(URL+'/api/embed', data=body, headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.load(resp)['embeddings']

def main():
    with psycopg.connect(os.environ['DATABASE_URL'], row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute('CREATE EXTENSION IF NOT EXISTS vector')
            cur.execute('CREATE TABLE IF NOT EXISTS legislation_embeddings (provision_id bigint PRIMARY KEY REFERENCES legislation_provisions(id) ON DELETE CASCADE, embedding vector(768) NOT NULL, model text NOT NULL, indexed_at timestamptz NOT NULL DEFAULT now())')
            conn.commit()
            cur.execute('''SELECT p.id, d.title, p.heading, p.body_text FROM legislation_provisions p JOIN legislation_documents d ON d.id=p.document_id LEFT JOIN legislation_embeddings e ON e.provision_id=p.id AND e.model=%s WHERE e.provision_id IS NULL ORDER BY p.id''', (MODEL,))
            records=cur.fetchall()
            print(f'Indexing {len(records)} provisions locally using {MODEL}', flush=True)
            for start in range(0, len(records), 8):
                batch=records[start:start+8]
                texts=[f"{r['title']} — {r['heading'] or ''}\n{r['body_text'][:6000]}" for r in batch]
                vectors=embed(texts)
                for record, vector in zip(batch, vectors):
                    if len(vector)!=768: raise RuntimeError(f'Expected 768 dimensions; got {len(vector)}')
                    cur.execute('''INSERT INTO legislation_embeddings (provision_id,embedding,model) VALUES (%s,%s::vector,%s) ON CONFLICT(provision_id) DO UPDATE SET embedding=excluded.embedding, model=excluded.model, indexed_at=now()''', (record['id'], '['+','.join(map(str,vector))+']', MODEL))
                conn.commit()
                print(f'{min(start+8,len(records))}/{len(records)}', flush=True)
            cur.execute('CREATE INDEX IF NOT EXISTS legislation_embeddings_hnsw ON legislation_embeddings USING hnsw (embedding vector_cosine_ops)')
            conn.commit()
            print('Indexing complete.', flush=True)

if __name__=='__main__': main()
