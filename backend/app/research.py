"""Local-only legal research API: PostgreSQL + Ollama. No paid APIs."""
import os
import json
import urllib.request
import urllib.error
import psycopg
from psycopg.rows import dict_row
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

router=APIRouter()
OLLAMA=os.getenv('OLLAMA_URL','http://host.docker.internal:11434').rstrip('/')
EMBED_MODEL=os.getenv('OLLAMA_EMBED_MODEL','nomic-embed-text')
CHAT_MODEL=os.getenv('OLLAMA_CHAT_MODEL','llama3.2:3b')

def ollama(endpoint, payload, timeout=120):
    req=urllib.request.Request(OLLAMA+endpoint, data=json.dumps(payload).encode(), headers={'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(req,timeout=timeout) as response: return json.load(response)
    except (urllib.error.URLError, TimeoutError) as exc:
        raise HTTPException(503,'Local Ollama unavailable. Start Ollama and pull the models.') from exc

def embed(q):
    vec=ollama('/api/embed', {'model':EMBED_MODEL,'input':q})['embeddings'][0]
    if len(vec)!=768: raise HTTPException(503,'Embedding dimension mismatch; expected nomic-embed-text (768).')
    return '['+','.join(map(str,vec))+']'

def find(q,limit=10,year=None,mode='keyword'):
    if mode not in ('keyword','semantic','hybrid'): raise HTTPException(422,'Invalid mode')
    vec=embed(q) if mode!='keyword' else None
    sql='''WITH lexical AS (
      SELECT p.id, row_number() OVER (ORDER BY ts_rank_cd(p.search_vector, websearch_to_tsquery('english',%(q)s)) DESC,p.id) AS rn
      FROM legislation_provisions p JOIN legislation_documents d ON d.id=p.document_id
      WHERE p.search_vector @@ websearch_to_tsquery('english',%(q)s) AND (%(year)s::integer IS NULL OR d.act_year=%(year)s::integer)
      ORDER BY ts_rank_cd(p.search_vector,websearch_to_tsquery('english',%(q)s)) DESC LIMIT 100
    ), semantic AS (
      SELECT e.provision_id AS id, row_number() OVER (ORDER BY e.embedding <=> %(vec)s::vector,e.provision_id) AS rn
      FROM legislation_embeddings e JOIN legislation_provisions p ON p.id=e.provision_id JOIN legislation_documents d ON d.id=p.document_id
      WHERE e.model=%(model)s
        AND (%(year)s::integer IS NULL OR d.act_year=%(year)s::integer)
        AND (e.embedding <=> %(vec)s::vector) < 0.45
      ORDER BY e.embedding <=> %(vec)s::vector LIMIT 100
    ), ranks AS (
      SELECT id,sum(score) score FROM (
        SELECT id,1.0/(60+rn) score FROM lexical WHERE %(mode)s IN ('keyword','hybrid')
        UNION ALL SELECT id,1.0/(60+rn) score FROM semantic WHERE %(mode)s IN ('semantic','hybrid')
      ) x GROUP BY id
    ) SELECT p.id,p.kind,p.provision_number,p.heading,left(p.body_text,3500) excerpt,
      d.title,d.act_year,d.act_number,d.source_version,d.source_url,d.canonical_uri,p.structural_path,ranks.score
      FROM ranks JOIN legislation_provisions p ON p.id=ranks.id JOIN legislation_documents d ON d.id=p.document_id
      ORDER BY ranks.score DESC,p.id LIMIT %(limit)s'''
    keyword='''SELECT p.id,p.kind,p.provision_number,p.heading,left(p.body_text,3500) excerpt,
      d.title,d.act_year,d.act_number,d.source_version,d.source_url,d.canonical_uri,p.structural_path,
      ts_rank_cd(p.search_vector,websearch_to_tsquery('english',%(q)s)) score
      FROM legislation_provisions p JOIN legislation_documents d ON d.id=p.document_id
      WHERE p.search_vector @@ websearch_to_tsquery('english',%(q)s) AND (%(year)s::integer IS NULL OR d.act_year=%(year)s::integer)
      ORDER BY score DESC,p.id LIMIT %(limit)s'''
    try:
        with psycopg.connect(os.environ['DATABASE_URL'],row_factory=dict_row) as conn,conn.cursor() as cur:
            if mode!='keyword':
                cur.execute("SELECT to_regclass('public.legislation_embeddings') AS name")
                if not cur.fetchone()['name']: raise HTTPException(503,'Run the local embedding indexer first.')
                cur.execute('SELECT count(*) n FROM legislation_embeddings WHERE model=%s',(EMBED_MODEL,))
                if not cur.fetchone()['n']: raise HTTPException(503,'Run the local embedding indexer first.')
            cur.execute(keyword if mode=='keyword' else sql,{'q':q,'limit':limit,'year':year,'vec':vec,'model':EMBED_MODEL,'mode':mode})
            return cur.fetchall()
    except psycopg.Error as exc:
        raise HTTPException(503,'Database retrieval error; check backend logs.') from exc

@router.get('/api/research/search')
def search(q:str=Query(min_length=2,max_length=300),limit:int=Query(15,ge=1,le=30),year:int|None=Query(None,ge=1922,le=2100),mode:str=Query('keyword',pattern='^(keyword|semantic|hybrid)$')):
    results=find(q,limit,year,mode)
    return {'query':q,'mode':mode,'count':len(results),'results':results,'notice':'Enacted legislation only; may not reflect current law.'}

class AskRequest(BaseModel):
    question:str=Field(min_length=5,max_length=300)
    mode:str=Field(default='hybrid',pattern='^(keyword|semantic|hybrid)$')
    year:int|None=None

@router.post('/api/research/ask')
def ask(request:AskRequest):
    hits=find(request.question,12,request.year,request.mode)
    hits=[
        h for h in hits
        if h['provision_number']
        and h['kind'].lower() not in ('part','chapter','heading')
    ][:6]
    if not hits:
        return {
            'answer': (
                'I could not find sufficiently relevant provisions '
                'in the currently imported Irish legislation. '
                'This does not mean Irish law contains no relevant provisions.'
            ),
            'sources': [],
            'status': 'insufficient_evidence',
            'notice': 'Verify against current official legislation.'
        }
    sources=[{'number':i,'title':r['title'],'act_year':r['act_year'],'provision_number':r['provision_number'],'heading':r['heading'],'url':r['canonical_uri'] or r['source_url'],'excerpt':r['excerpt']} for i,r in enumerate(hits,1)]
    evidence='\n\n'.join(f"[{s['number']}] {s['title']}, provision {s['provision_number'] or 'unnumbered'}: {s['excerpt']}" for s in sources)
    messages=[{'role':'system','content':'You are an Irish legislation research assistant. Use ONLY the supplied legislative evidence. Cite each substantive legal claim using the evidence numbers [1], [2], etc. Do not invent legal rules, citations, or subsection references. Do not attribute a rule to a section unless that section supports it. Avoid repetition. If evidence is insufficient, say so. This corpus contains enacted text and may not reflect amendments, commencement or current law. Be concise; not legal advice.'},{'role':'user','content':f'Question: {request.question}\n\nEvidence:\n{evidence}'}]
    response=ollama('/api/chat',{'model':CHAT_MODEL,'messages':messages,'stream':False,'options':{'temperature':0.1,'num_predict':700}},timeout=180)
    return {'answer':response.get('message',{}).get('content','No answer returned.'),'sources':sources,'notice':'Verify against the current official law; not legal advice.'}
