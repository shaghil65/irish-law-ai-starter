"""Run: python -m app.index_embeddings --batch-size 32 [--max-items 100]"""
import argparse
import os
import time
import psycopg
from openai import OpenAI

MODEL = 'text-embedding-3-small'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--batch-size', type=int, default=32)
    parser.add_argument('--max-items', type=int, default=0)
    args = parser.parse_args()
    if not 1 <= args.batch_size <= 100:
        parser.error('--batch-size must be between 1 and 100')
    if not os.getenv('OPENAI_API_KEY'):
        parser.error('OPENAI_API_KEY is required')
    api = OpenAI(timeout=90, max_retries=3)
    with psycopg.connect(os.environ['DATABASE_URL']) as conn:
        with conn.cursor() as cur:
            cur.execute('CREATE EXTENSION IF NOT EXISTS vector')
            cur.execute('''CREATE TABLE IF NOT EXISTS legislation_embeddings (
                provision_id bigint PRIMARY KEY REFERENCES legislation_provisions(id) ON DELETE CASCADE,
                embedding vector(1536) NOT NULL, model text NOT NULL,
                indexed_at timestamptz NOT NULL DEFAULT now())''')
            cur.execute('''CREATE INDEX IF NOT EXISTS legislation_embeddings_hnsw
                ON legislation_embeddings USING hnsw (embedding vector_cosine_ops)''')
        conn.commit()
        total = 0
        while True:
            with conn.cursor() as cur:
                cur.execute('''SELECT p.id, d.title, p.heading, p.body_text
                    FROM legislation_provisions p JOIN legislation_documents d ON d.id=p.document_id
                    LEFT JOIN legislation_embeddings e ON e.provision_id=p.id
                    WHERE e.provision_id IS NULL OR e.model != %s
                    ORDER BY p.id LIMIT %s''', (MODEL, args.batch_size if not args.max_items else min(args.batch_size, args.max_items-total)))
                rows = cur.fetchall()
            if not rows:
                break
            inputs = [(f'{title}\n{heading or ""}\n{body}')[:7500] for _, title, heading, body in rows]
            response = api.embeddings.create(model=MODEL, input=inputs)
            vectors = {entry.index: entry.embedding for entry in response.data}
            with conn.cursor() as cur:
                for i, row in enumerate(rows):
                    vector = '[' + ','.join(map(str, vectors[i])) + ']'
                    cur.execute('''INSERT INTO legislation_embeddings(provision_id, embedding, model)
                      VALUES (%s, %s::vector, %s) ON CONFLICT (provision_id) DO UPDATE SET
                      embedding=excluded.embedding, model=excluded.model, indexed_at=now()''', (row[0], vector, MODEL))
            conn.commit()
            total += len(rows)
            print(f'Indexed {total} provisions this run', flush=True)
            if args.max_items and total >= args.max_items:
                break
            time.sleep(0.1)
    print('Indexing complete.')

if __name__ == '__main__':
    main()
