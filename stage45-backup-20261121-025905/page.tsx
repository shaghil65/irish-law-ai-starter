"use client";

import { useState } from "react";

type Result = {
  id: number; kind: string; provision_number: string | null; heading: string | null;
  excerpt: string; title: string; act_year: number; act_number: number;
  source_version: string; source_url: string; canonical_uri: string; structural_path: string;
};
type SearchResponse = { query: string; count: number; results: Result[]; corpus: string };

export default function Home() {
  const [q, setQ] = useState("");
  const [year, setYear] = useState("");
  const [data, setData] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  async function search(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (q.trim().length < 2) return;
    setLoading(true); setError(""); setData(null);
    try {
      const params = new URLSearchParams({ q: q.trim(), limit: "25" });
      if (year) params.set("year", year);
      const response = await fetch(`${apiUrl}/api/search?${params.toString()}`);
      if (!response.ok) throw new Error(`Search failed (HTTP ${response.status})`);
      setData(await response.json());
    } catch (e) { setError(e instanceof Error ? e.message : "Search unavailable"); }
    finally { setLoading(false); }
  }

  return (
    <main className="searchShell">
      <header className="searchHeader"><span className="brand"><span className="brandMark">§</span> Irish Law AI</span><span className="topTag">STAGE 3 · LEGAL SEARCH</span></header>
      <section className="searchHero">
        <p className="eyebrow">IRISH LEGISLATION RESEARCH</p>
        <h1>Find the law.<br /><em>Read the source.</em></h1>
        <p className="intro">Search imported Irish Acts and inspect the underlying provisions. Results link to the official Irish Statute Book.</p>
        <form onSubmit={search} className="searchForm">
          <label htmlFor="search" className="miniLabel">SEARCH LEGISLATION</label>
          <div className="searchControls">
            <input id="search" value={q} onChange={e => setQ(e.target.value)} placeholder="e.g. district court jurisdiction" minLength={2} maxLength={300} required />
            <input aria-label="Filter by Act year" value={year} onChange={e => setYear(e.target.value)} placeholder="Year (optional)" type="number" min="1922" max="2100" />
            <button type="submit" disabled={loading}>{loading ? "Searching…" : "Search"}</button>
          </div>
        </form>
        <p className="legalNotice">Research preview · Enacted legislation only. Provisions may have been amended, repealed or not commenced. Not legal advice.</p>
      </section>
      {error && <p role="alert" className="searchError">{error}</p>}
      {data && <section className="searchResults" aria-live="polite">
        <h2>{data.count} matching provisions{data.count === 25 ? " (first 25)" : ""}</h2>
        {data.results.length === 0 && <p>No matches in the imported corpus. Try broader terms or remove the year filter.</p>}
        {data.results.map(item => <article className="resultCard" key={item.id}>
          <p className="resultMeta">{item.act_year} · Act No. {item.act_number} · {item.source_version}</p>
          <h3>{item.title}</h3>
          <p className="resultHeading">{item.kind}{item.provision_number ? ` ${item.provision_number}` : ""}{item.heading ? ` — ${item.heading}` : ""}</p>
          <p className="resultExcerpt">{item.excerpt}{item.excerpt.length >= 550 ? "…" : ""}</p>
          <a href={item.source_url} target="_blank" rel="noopener noreferrer">View official enacted Act ↗</a>
        </article>)}
      </section>}
    </main>
  );
}
