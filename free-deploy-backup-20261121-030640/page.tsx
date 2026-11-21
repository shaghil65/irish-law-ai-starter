"use client";
import { useState } from "react";

type Hit = {id:number; kind:string; provision_number:string|null; heading:string|null; excerpt:string; title:string; act_year:number; act_number:number; source_version:string; source_url:string; canonical_uri:string; score:number};
type Source = {number:number; title:string; act_year:number; provision_number:string|null; heading:string|null; url:string; excerpt:string};
const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
export default function Home() {
 const [q,setQ]=useState(""); const [year,setYear]=useState(""); const [mode,setMode]=useState("keyword");
 const [results,setResults]=useState<Hit[]|null>(null); const [answer,setAnswer]=useState<string|null>(null);
 const [sources,setSources]=useState<Source[]>([]); const [busy,setBusy]=useState(false); const [error,setError]=useState("");
 async function run(ask:boolean) {
  if(q.trim().length<2) return; setBusy(true); setError(""); setAnswer(null); setSources([]); setResults(null);
  try {
   let response:Response;
   if(ask) response=await fetch(`${API}/api/research/ask`, {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({question:q.trim(),mode,year:year?Number(year):null})});
   else {const params=new URLSearchParams({q:q.trim(),mode,limit:"20"});if(year)params.set("year",year);response=await fetch(`${API}/api/research/search?${params}`);}
   const payload=await response.json(); if(!response.ok) throw new Error(payload.detail||`HTTP ${response.status}`);
   if(ask){setAnswer(payload.answer);setSources(payload.sources||[]);}else setResults(payload.results||[]);
  }catch(e){setError(e instanceof Error?e.message:"Request failed");}finally{setBusy(false);}
 }
 return <main className="searchShell">
  <header className="searchHeader"><span className="brand"><span className="brandMark">§</span> Irish Law AI</span><span className="topTag">LEGAL RESEARCH · STAGES 3–5</span></header>
  <section className="searchHero"><p className="eyebrow">IRISH LEGISLATION RESEARCH</p><h1>Find the law.<br/><em>Check the source.</em></h1>
   <p className="intro">Keyword and semantic retrieval over imported Irish Acts, with evidence-grounded AI research answers.</p>
   <form className="searchForm" onSubmit={e=>{e.preventDefault();void run(false);}}>
    <label className="miniLabel" htmlFor="legalQuery">SEARCH LEGISLATION</label>
    <div className="searchControls"><input id="legalQuery" value={q} onChange={e=>setQ(e.target.value)} minLength={2} maxLength={300} placeholder="e.g. family court jurisdiction" required/>
     <input aria-label="Filter by Act year" type="number" min="1922" max="2100" placeholder="Year" value={year} onChange={e=>setYear(e.target.value)}/>
     <button type="submit" disabled={busy||q.trim().length<2}>{busy?"Working…":"Search"}</button></div>
    <div className="researchOptions"><label htmlFor="searchMode">Search mode</label><select id="searchMode" value={mode} onChange={e=>setMode(e.target.value)}><option value="keyword">Keyword (no API key needed)</option><option value="hybrid">Hybrid (keyword + semantic)</option><option value="semantic">Semantic (meaning-based)</option></select>
     <button type="button" disabled={busy||q.trim().length<5} onClick={()=>void run(true)}>Ask AI with citations</button></div>
   </form><p className="legalNotice">Research preview · Enacted legislation only. Provisions may be amended, repealed or not commenced. Not legal advice. AI answers may be inaccurate; verify all citations.</p>
  </section>
  {error&&<p role="alert" className="searchError">{error}</p>}
  {results&&<section className="searchResults" aria-live="polite"><h2>{results.length} retrieved provisions</h2>{results.length===0&&<p>No matches in the imported corpus. Try broader terms or another mode.</p>}
   {results.map(r=><article className="resultCard" key={r.id}><p className="resultMeta">{r.act_year} · Act No. {r.act_number} · {r.source_version}</p><h3>{r.title}</h3><p className="resultHeading">{r.kind} {r.provision_number} {r.heading?`— ${r.heading}`:""}</p><p className="resultExcerpt">{r.excerpt}…</p><a href={r.canonical_uri} target="_blank" rel="noopener noreferrer">Official enacted Act ↗</a></article>)}
  </section>}
  {answer!==null&&<section className="searchResults" aria-live="polite"><h2>AI research answer</h2><article className="resultCard"><p className="aiAnswer">{answer}</p><p className="legalNotice">Citation numbers refer to the evidence list below. Verify against official sources.</p></article><h2>Evidence cited / retrieved</h2>
   {sources.map(s=><article className="resultCard" key={s.number}><p className="resultMeta">[{s.number}] {s.act_year}</p><h3>{s.title}</h3><p className="resultHeading">Section {s.provision_number} {s.heading}</p><p className="resultExcerpt">{s.excerpt}…</p><a href={s.url} target="_blank" rel="noopener noreferrer">Official enacted Act ↗</a></article>)}
  </section>}
 </main>;
}
