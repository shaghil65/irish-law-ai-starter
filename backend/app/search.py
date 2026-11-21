import os
from typing import Optional
import psycopg
from fastapi import APIRouter, HTTPException, Query
from psycopg.rows import dict_row

router = APIRouter()

@router.get('/api/search')
def search(q: str = Query(min_length=2, max_length=300), limit: int = Query(20, ge=1, le=50), year: Optional[int] = Query(None, ge=1922, le=2100)):
    sql = '''
    WITH terms AS (SELECT websearch_to_tsquery('english', %(q)s) AS query)
    SELECT p.id, p.kind, p.provision_number, p.heading,
           LEFT(p.body_text, 550) AS excerpt,
           d.title, d.act_year, d.act_number, d.source_version, d.source_url,
           d.canonical_uri, p.structural_path,
           (
           ts_rank_cd(p.search_vector, terms.query)
           + 2.0 * ts_rank_cd(
               to_tsvector('english', COALESCE(d.title, '')),
               terms.query
           )
           + 1.5 * ts_rank_cd(
               to_tsvector('english', COALESCE(p.heading, '')),
               terms.query
           )
       ) AS rank
    FROM legislation_provisions p
    JOIN legislation_documents d ON d.id = p.document_id
    CROSS JOIN terms
    WHERE p.search_vector @@ terms.query
      AND (%(year)s::integer IS NULL OR d.act_year = %(year)s::integer)
    ORDER BY rank DESC, d.act_year DESC, p.position ASC
    LIMIT %(limit)s
    '''
    try:
        with psycopg.connect(os.environ['DATABASE_URL'], connect_timeout=5, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, {'q': q, 'year': year, 'limit': limit})
                results = cur.fetchall()
    except (psycopg.Error, KeyError) as exc:
        raise HTTPException(status_code=503, detail='Legal search database unavailable') from exc
    return {'query': q, 'results': results, 'count': len(results), 'search_mode': 'keyword', 'corpus': 'enacted legislation; may not reflect current law'}
